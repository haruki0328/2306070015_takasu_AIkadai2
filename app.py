# app.py (アカウント機能追加版)

import streamlit as st
from logic import (
    search_books, load_reviews, save_review, 
    get_ranking_data, get_user_reviews,
    register_user, verify_user
)

st.set_page_config(layout="wide")

# ----------------------------------------------------------------
# ログイン状態の確認
# ----------------------------------------------------------------
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# ----------------------------------------------------------------
# ログイン／新規登録ページ
# ----------------------------------------------------------------
if not st.session_state.logged_in_user:
    st.title("📚 おすすめ本棚アプリへようこそ")
    
    login_tab, signup_tab = st.tabs(["ログイン", "新規登録"])
    
    # --- ログインタブ ---
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("ユーザー名")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン")
            if submitted:
                if verify_user(username, password):
                    st.session_state.logged_in_user = username
                    st.rerun()
                else:
                    st.error("ユーザー名またはパスワードが間違っています。")
    
    # --- 新規登録タブ ---
    with signup_tab:
        with st.form("signup_form"):
            new_username = st.text_input("ユーザー名")
            new_password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("登録する")
            if submitted:
                success, message = register_user(new_username, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

# ----------------------------------------------------------------
# メインアプリページ (ログイン後)
# ----------------------------------------------------------------
else:
    # --- ヘッダーとログアウト ---
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title(f"📚 {st.session_state.logged_in_user}さんの本棚")
    with col2:
        if st.button("ログアウト"):
            st.session_state.logged_in_user = None
            st.rerun()

    # --- レビューページ ---
    if "selected_book_id" in st.session_state:
        # (この部分は以前のコードとほぼ同じ。usernameの扱いだけ変更)
        # ...
        if st.button("← メインページに戻る"):
            del st.session_state.selected_book_id
            st.rerun()

        st.header(f"「{st.session_state.selected_book_title}」のレビュー")

        with st.form(f"review_form_{st.session_state.selected_book_id}", clear_on_submit=True):
            rating = st.slider("評価 (5段階)", 1, 5, 3)
            comment = st.text_area("コメント")
            submitted = st.form_submit_button("投稿")
            if submitted:
                # ログイン中のユーザー名を自動で使用
                save_review(
                    st.session_state.selected_book_id, 
                    st.session_state.selected_book_title, 
                    st.session_state.logged_in_user, 
                    rating, 
                    comment
                )
                st.success("レビューを投稿しました！")
                st.rerun()
    
    # --- メインページ ---
    else:
        st.write("本を検索したり、話題のカテゴリから新しい本を見つけよう！")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 キーワード検索", "🌟 カテゴリ検索", "🏆 ランキング", "👤 マイページ"])
        
        # (検索タブ、カテゴリタブ、ランキングタブは以前のコードとほぼ同じ)
        # ...

        # --- マイページタブ (修正) ---
        with tab4:
            st.subheader(f"{st.session_state.logged_in_user}さんの投稿履歴")
            # ログイン中のユーザーのレビューを自動で表示
            user_reviews = get_user_reviews(st.session_state.logged_in_user)
            if not user_reviews.empty:
                for index, row in user_reviews.iterrows():
                    st.markdown(f"**{row['book_title']}** (評価: {'★' * int(row['rating'])})")
                    st.info(f"コメント: {row['comment']}")
                    st.markdown("---")
            else:
                st.write("まだレビューを投稿していません。")
                
        # (検索結果表示部分は以前のコードとほぼ同じ)
        # ...

    st.markdown("---") # 区切り線

    # --- 検索結果の表示 ---
    if "search_results" in st.session_state and st.session_state.search_results:
        # (この部分は変更なし)
        st.subheader("書籍一覧")
        st.write("レビューしたい本を選んでください。")
        cols = st.columns(3)
        for i, book in enumerate(st.session_state.search_results):
            with cols[i % 3]:
                if book["cover_url"]:
                    st.image(book["cover_url"])
                else:
                    st.markdown("*(画像なし)*")
                st.write(f"**{book['title']}**")
                st.caption(f"著者: {book['author']}")
                if st.button("この本をレビューする", key=book["id"]):
                    st.session_state.selected_book_id = book['id']
                    st.session_state.selected_book_title = book['title']
                    st.rerun()