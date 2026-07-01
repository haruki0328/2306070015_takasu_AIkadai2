import os
import pandas as pd
import hashlib
import requests
import streamlit as st
import uuid
import random

# プロトタイプとしての迅速な検証を目的とし、DB構築が不要なCSVを永続化層として採用
REVIEW_FILE = "reviews.csv"
USER_FILE = "users.csv"
USER_BOOKS_FILE = "user_books.csv"

# ==========================================
# 認証・セキュリティロジック
# ==========================================

def hash_password(password):
    """
    セキュリティ対策：万が一ファイルが流出してもパスワードが復元されないよう、
    平文ではなくSHA-256アルゴリズムでハッシュ化して保存する。
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password_hash, provided_password):
    return stored_password_hash == hash_password(provided_password)

def register_user(username, password):
    """
    新規ユーザー登録処理。
    辞書攻撃やブルートフォース攻撃への耐性を高めるため、厳格なパスワードポリシーを適用する。
    """
    username = username.strip() if username else ""
    if not username:
        return False, "ユーザー名を入力してください。"

    # セキュリティ要件：8文字以上、大文字・小文字・数字の混在を必須とする
    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
        return False, "パスワードの条件を満たしていません。"

    # 初回実行時：ユーザー管理用のCSVが存在しなければヘッダー付きで新規作成
    if not os.path.exists(USER_FILE):
        pd.DataFrame(columns=["username", "password_hash"]).to_csv(USER_FILE, index=False)
    
    try:
        df = pd.read_csv(USER_FILE, dtype={"username": str})
    except Exception:
        df = pd.DataFrame(columns=["username", "password_hash"])
    
    # 重複登録の防止
    if username in df["username"].fillna("").tolist():
        return False, f"「{username}」は既に使用されています。"
    
    # パスワードは必ずハッシュ化してCSVの末尾に追記 (mode='a')
    new_user = {"username": [username], "password_hash": [hash_password(password)]}
    pd.DataFrame(new_user).to_csv(USER_FILE, mode='a', header=False, index=False)
    return True, "アカウントを作成しました。ログインしてください。"

def verify_user(username, password):
    """ログイン時の認証処理"""
    if not os.path.exists(USER_FILE): return False
    try:
        df = pd.read_csv(USER_FILE, dtype={"username": str})
        user_data = df[df["username"] == username]
        if not user_data.empty and verify_password(user_data.iloc[0]["password_hash"], password):
            return True
    except Exception:
        pass
    return False


# ==========================================
# 外部API通信・書籍データ取得ロジック
# ==========================================

def _fetch_search(query, limit):
    """
    Open Library APIを利用して書籍を検索するコア処理。
    APIサーバー遅延によるアプリのフリーズを防ぐため、10秒のタイムアウトを設定。
    """
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
    """
    ユーザーからの検索要求を処理する。
    APIの呼び出し過多（レートリミット）を防ぐため、同一クエリの結果を1時間キャッシュする。
    """
    if not query: return []
    query = query.strip()
    if not query: return []

    try:
        books = _fetch_search(query, limit)

        # UX向上（フェイルセーフ）機能：
        # 日本語でのスペース区切り検索（例：「ハリーポッター 1」）で0件になるAPIの仕様を補完するため、
        # 完全一致で見つからない場合は単語を分割して再検索を行う。
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
    """
    トップページ等で「おすすめ本」として表示するためのランダム抽出処理。
    幅広いジャンルを定義し、ユーザーの新しい本との出会いを創出する。
    """
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


# ==========================================
# レビュー＆ユーザー本棚管理ロジック
# ==========================================

def load_reviews(book_id):
    """指定された書籍のレビューを「いいね」が多い順に取得し、有用な評価を上位に表示する"""
    if not os.path.exists(REVIEW_FILE): return pd.DataFrame()
    df = pd.read_csv(REVIEW_FILE)
    df["comment"] = df["comment"].fillna("") # 未入力コメントがNaN("nan"表示)になるのを防ぐ
    return df[df["book_id"] == book_id].sort_values(by="likes", ascending=False)

def save_review(book_id, book_title, author, cover_url, username, rating, comment):
    """
    レビューの保存処理。
    重複や判別エラーを防ぐため、UUIDを用いて各レビューに一意のIDを付与する。
    """
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
    """
    トレンド分析：
    レビュー投稿数（話題性）と平均スコア（高評価）の2軸でランキングを集計する。
    データの更新頻度を考慮し、キャッシュ期間は10秒と短めに設定。
    """
    if not os.path.exists(REVIEW_FILE): return pd.DataFrame(), pd.DataFrame()
    df = pd.read_csv(REVIEW_FILE)
    if df.empty: return pd.DataFrame(), pd.DataFrame()
    
    most_reviewed = df.groupby('book_id').agg({'book_title':'first', 'author':'first', 'cover_url':'first', 'book_id':'size'}).rename(columns={'book_id': 'review_count'}).sort_values(by='review_count', ascending=False).head(5).reset_index()
    top_rated = df.groupby('book_id').agg({'book_title':'first', 'author':'first', 'cover_url':'first', 'rating':'mean'}).rename(columns={'rating': 'avg_rating'}).sort_values(by='avg_rating', ascending=False).head(5).reset_index()
    return most_reviewed, top_rated

def update_book_status(username, book_id, book_title, cover_url, status):
    """
    ユーザー個人の読書ステータス（読了/読書中など）を更新する。
    既に登録済みの本であれば状態をUPDATEし、未登録であればINSERTする（UPSERT処理）。
    """
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
    """ユーザーの本棚データを取得する。ファイルやカラムが存在しない場合のエラーを回避する安全設計。"""
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