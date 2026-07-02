import os
import pandas as pd
import hashlib
import requests
import streamlit as st
import uuid
import random

REVIEW_FILE = "reviews.csv"
USER_FILE = "users.csv"
USER_BOOKS_FILE = "user_books.csv"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password_hash, provided_password):
    return stored_password_hash == hash_password(provided_password)

def register_user(username, password):
    username = username.strip() if username else ""
    if not username:
        return False, "ユーザー名を入力してください。"

    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
        return False, "パスワードの条件を満たしていません。"

    if not os.path.exists(USER_FILE):
        pd.DataFrame(columns=["username", "password_hash"]).to_csv(USER_FILE, index=False)

    try:
        df = pd.read_csv(USER_FILE, dtype={"username": str})
    except Exception:
        df = pd.DataFrame(columns=["username", "password_hash"])

    if username in df["username"].fillna("").tolist():
        return False, f"「{username}」は既に使用されています。"

    new_user = {"username": [username], "password_hash": [hash_password(password)]}
    pd.DataFrame(new_user).to_csv(USER_FILE, mode='a', header=False, index=False)
    return True, "アカウントを作成しました。ログインしてください。"

def verify_user(username, password):
    if not os.path.exists(USER_FILE): return False
    try:
        df = pd.read_csv(USER_FILE, dtype={"username": str})
        user_data = df[df["username"] == username]
        if not user_data.empty and verify_password(user_data.iloc[0]["password_hash"], password):
            return True
    except Exception:
        pass
    return False


def _fetch_search(query, limit):
    response = requests.get(
        "https://openlibrary.org/search.json",
        params={"q": query, "limit": limit},
        timeout=10
    )
    response.raise_for_status()

    books = []
    for doc in response.json().get("docs", [])[:limit]:
        book_id = doc.get("key")
        title = doc.get("title")
        author = ", ".join(doc.get("author_name", ["不明な著者"]))
        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None

        if book_id and title:
            books.append({"id": book_id, "title": title, "author": author, "cover_url": cover_url})
    return books

@st.cache_data(ttl=3600)
def search_books(query, limit=12):
    if not query: return []
    query = query.strip()
    if not query: return []

    try:
        books = _fetch_search(query, limit)

        # 「ハリーポッター 1」のようなスペース入り検索で0件になることがあるので、
        # 単語ごとに分けて再検索する
        if not books and " " in query:
            for word in query.split():
                if len(word) < 2:
                    continue
                books = _fetch_search(word, limit)
                if books:
                    break

        return books
    except Exception:
        return []

@st.cache_data(ttl=600)
def get_random_books(limit=12):
    RANDOM_SUBJECTS = [
        "fiction", "fantasy", "mystery", "science_fiction", "romance",
        "history", "biography", "business", "self_help", "poetry",
        "cooking", "art", "philosophy", "programming", "psychology",
    ]
    try:
        subject = random.choice(RANDOM_SUBJECTS)
        offset = random.randint(0, 80)
        response = requests.get(
            f"https://openlibrary.org/subjects/{subject}.json",
            params={"limit": limit, "offset": offset},
            timeout=10
        )
        response.raise_for_status()
        works = response.json().get("works", [])

        books = []
        for w in works:
            book_id = w.get("key")
            title = w.get("title")
            authors = w.get("authors", [])
            author = ", ".join(a.get("name", "") for a in authors) if authors else "不明な著者"
            cover_id = w.get("cover_id")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None

            if book_id and title:
                books.append({"id": book_id, "title": title, "author": author, "cover_url": cover_url})

        random.shuffle(books)
        return books
    except Exception:
        return []


def load_reviews(book_id):
    if not os.path.exists(REVIEW_FILE): return pd.DataFrame()
    df = pd.read_csv(REVIEW_FILE)
    df["comment"] = df["comment"].fillna("")
    return df[df["book_id"] == book_id].sort_values(by="likes", ascending=False)

def save_review(book_id, book_title, author, cover_url, username, rating, comment):
    review_id = str(uuid.uuid4())
    new_review = {
        "review_id": [review_id],
        "book_id": [book_id],
        "book_title": [book_title],
        "author": [author],
        "cover_url": [cover_url],
        "username": [username],
        "rating": [rating],
        "comment": [comment],
        "likes": [0]
    }
    df = pd.DataFrame(new_review)
    df.to_csv(REVIEW_FILE, mode='a', header=not os.path.exists(REVIEW_FILE), index=False)

def increment_like(review_id):
    if not os.path.exists(REVIEW_FILE): return
    df = pd.read_csv(REVIEW_FILE)
    df.loc[df["review_id"] == review_id, "likes"] += 1
    df.to_csv(REVIEW_FILE, index=False)

@st.cache_data(ttl=10)
def get_ranking_data():
    if not os.path.exists(REVIEW_FILE): return pd.DataFrame(), pd.DataFrame()
    df = pd.read_csv(REVIEW_FILE)
    if df.empty: return pd.DataFrame(), pd.DataFrame()

    most_reviewed = df.groupby('book_id').agg({'book_title':'first', 'author':'first', 'cover_url':'first', 'book_id':'size'}).rename(columns={'book_id': 'review_count'}).sort_values(by='review_count', ascending=False).head(5).reset_index()
    top_rated = df.groupby('book_id').agg({'book_title':'first', 'author':'first', 'cover_url':'first', 'rating':'mean'}).rename(columns={'rating': 'avg_rating'}).sort_values(by='avg_rating', ascending=False).head(5).reset_index()
    return most_reviewed, top_rated

def update_book_status(username, book_id, book_title, cover_url, status):
    if not os.path.exists(USER_BOOKS_FILE):
        pd.DataFrame(columns=["username", "book_id", "book_title", "cover_url", "status"]).to_csv(USER_BOOKS_FILE, index=False)

    df = pd.read_csv(USER_BOOKS_FILE)
    mask = (df["username"] == username) & (df["book_id"] == book_id)

    if not df[mask].empty:
        df.loc[mask, "status"] = status
    else:
        new_row = pd.DataFrame({"username": [username], "book_id": [book_id], "book_title": [book_title], "cover_url": [cover_url], "status": [status]})
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(USER_BOOKS_FILE, index=False)

def get_user_books(username):
    if not os.path.exists(USER_BOOKS_FILE):
        return pd.DataFrame(columns=["username", "book_id", "book_title", "cover_url", "status"])

    df = pd.read_csv(USER_BOOKS_FILE)

    if "status" not in df.columns:
        return pd.DataFrame(columns=["username", "book_id", "book_title", "cover_url", "status"])

    return df[df["username"] == username]

def get_book_status(username, book_id):
    if not os.path.exists(USER_BOOKS_FILE): return "未登録"
    df = pd.read_csv(USER_BOOKS_FILE)
    user_book = df[(df["username"] == username) & (df["book_id"] == book_id)]
    if not user_book.empty:
        return user_book.iloc[0]["status"]
    return "未登録"
