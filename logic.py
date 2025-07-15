import requests
import pandas as pd
import os
import hashlib # パスワードのハッシュ化に使用

# ファイル定義
REVIEW_FILE = "reviews.csv"
USER_FILE = "users.csv"

# --- アカウント管理関数 (新規追加) ---

def hash_password(password):
    """パスワードをハッシュ化する"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password_hash, provided_password):
    """入力されたパスワードが保存されたハッシュと一致するか検証する"""
    return stored_password_hash == hash_password(provided_password)

def register_user(username, password):
    """ユーザーを新規登録する"""
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["username", "password_hash"])
        df.to_csv(USER_FILE, index=False)
    
    df = pd.read_csv(USER_FILE)
    if username in df["username"].values:
        return False, "このユーザー名は既に使用されています。"
    
    new_user = {
        "username": [username],
        "password_hash": [hash_password(password)]
    }
    pd.DataFrame(new_user).to_csv(USER_FILE, mode='a', header=False, index=False)
    return True, "登録が完了しました。"

def verify_user(username, password):
    """ユーザーのログインを認証する"""
    if not os.path.exists(USER_FILE):
        return False
        
    df = pd.read_csv(USER_FILE)
    user_data = df[df["username"] == username]
    
    if not user_data.empty:
        stored_hash = user_data.iloc[0]["password_hash"]
        if verify_password(stored_hash, password):
            return True
    return False


def search_books(query):
    """Open Library APIを使って書籍を検索する"""
    if not query:
        return []
    
    try:
        url = f"https://openlibrary.org/search.json?q={query}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for doc in data.get("docs", [])[:9]: # 3列表示のため9件に調整
            book_id = doc.get("key")
            title = doc.get("title")
            author = ", ".join(doc.get("author_name", ["N/A"]))
            cover_id = doc.get("cover_i")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
            
            if book_id and title:
                books.append({
                    "id": book_id,
                    "title": title,
                    "author": author,
                    "cover_url": cover_url
                })
        return books
    except requests.exceptions.RequestException as e:
        print(f"APIリクエストエラー: {e}")
        return []

def load_reviews(book_id):
    """特定の書籍IDのレビューをCSVファイルから読み込む"""
    if not os.path.exists(REVIEW_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(REVIEW_FILE)
        return df[df["book_id"] == book_id]
    except pd.errors.EmptyDataError:
        return pd.DataFrame()

def save_review(book_id, book_title, username, rating, comment):
    """レビューをCSVファイルに保存する"""
    new_review = {
        "book_id": [book_id],
        "book_title": [book_title],
        "username": [username],
        "rating": [rating],
        "comment": [comment]
    }
    df = pd.DataFrame(new_review)
    
    header = not os.path.exists(REVIEW_FILE)
    df.to_csv(REVIEW_FILE, mode='a', header=header, index=False)

def get_ranking_data():
    """レビューデータを集計してランキング情報を返す"""
    if not os.path.exists(REVIEW_FILE):
        return pd.DataFrame(), pd.DataFrame()

    df = pd.read_csv(REVIEW_FILE)
    
    if 'book_title' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    most_reviewed = df.groupby(['book_id', 'book_title']).size().reset_index(name='review_count')
    most_reviewed = most_reviewed.sort_values(by='review_count', ascending=False).head(5)

    top_rated = df.groupby(['book_id', 'book_title'])['rating'].mean().reset_index()
    top_rated = top_rated.sort_values(by='rating', ascending=False).head(5)
    
    return most_reviewed, top_rated

def get_user_reviews(username):
    """特定のユーザーのレビュー履歴を取得する"""
    if not os.path.exists(REVIEW_FILE) or not username:
        return pd.DataFrame()
        
    df = pd.read_csv(REVIEW_FILE)

    if 'book_title' not in df.columns:
        return pd.DataFrame()

    return df[df["username"] == username]