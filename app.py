import streamlit as st
from logic import (
    search_books, load_reviews, save_review, 
    get_ranking_data, get_user_reviews,
    register_user, verify_user,
    add_to_wishlist, get_wishlist, is_in_wishlist
)

# ページ設定はスクリプトの最初に一度だけ呼び出す
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
            # ログアウト時にセッション情報をクリア
            for key in list(st.session_state.keys()):
                if key != 'logged_in_user':
                    del st.session_state[key]
            st.session_state.logged_in_user = None
            st.rerun()

    # --- レビューページ ---
    if "selected_book_id" in st.session_state:
        book_id = st.session_state.selected_book_id
        book_title = st.session_state.selected_book_title

        if st.button("← メインページに戻る"):
            del st.session_state.selected_book_id
            if "selected_book_title" in st.session_state:
                del st.session_state.selected_book_title
            st.rerun()

        st.header(f"「{book_title}」のレビュー")

        # ▼▼▼ 抜けていたレビュー表示部分 ▼▼▼
        st.subheader("投稿されたレビュー")
        reviews_df = load_reviews(book_id)
        if not reviews_df.empty:
            for index, row in reviews_df.iterrows():
                st.markdown(f"**{row['username']}** さん (評価: {'★' * int(row['rating'])})")
                st.info(row['comment'])
                st.markdown("---")
        else:
            st.write("まだレビューはありません。")
        # ▲▲▲ ここまで ▲▲▲

        st.subheader("レビューを投稿する")
        with st.form(f"review_form_{book_id}", clear_on_submit=True):
            rating = st.slider("評価 (5段階)", 1, 5, 3)
            comment = st.text_area("コメント")
            submitted = st.form_submit_button("投稿")
            if submitted:
                save_review(
                    book_id, 
                    book_title, 
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
        
        # ▼▼▼ 抜けていたタブの中身 ▼▼▼
        with tab1:
            search_query = st.text_input("書籍名や著者名を入力", key="search_input")
            if st.button("検索", key="search_button"):
                with st.spinner("検索中..."):
                    st.session_state.search_results = search_books(search_query)
                st.rerun()
        
        with tab2:
            categories = ["love", "adventure", "fantasy", "mystery", "science_fiction", "history"]
            selected_category = st.selectbox("興味のあるカテゴリを選んでください", categories)
            if st.button("このカテゴリで探す", key="category_button"):
                with st.spinner(f"「{selected_category}」カテゴリの本を探しています..."):
                    st.session_state.search_results = search_books(selected_category)
                st.rerun()
        
        with tab3:
            st.subheader("レビューランキング")
            most_reviewed, top_rated = get_ranking_data()
            
            st.markdown("#### レビュー数 TOP5")
            if not most_reviewed.empty:
                st.dataframe(most_reviewed[['book_title', 'review_count']].rename(columns={'book_title': '書籍名', 'review_count': 'レビュー数'}), use_container_width=True)
            else:
                st.write("まだレビューがありません。")

            st.markdown("#### 評価点 TOP5")
            if not top_rated.empty:
                st.dataframe(top_rated[['book_title', 'rating']].rename(columns={'book_title': '書籍名', 'rating': '平均評価'}).style.format({'平均評価': '{:.2f}'}), use_container_width=True)
            else:
                st.write("まだレビューがありません。")
        
        with tab4:
            st.subheader(f"{st.session_state.logged_in_user}さんの投稿履歴")
            user_reviews = get_user_reviews(st.session_state.logged_in_user)
            if not user_reviews.empty:
                for index, row in user_reviews.iterrows():
                    st.markdown(f"**{row['book_title']}** (評価: {'★' * int(row['rating'])})")
                    st.info(f"コメント: {row['comment']}")
                    st.markdown("---")
            else:
                st.write("まだレビューを投稿していません。")
            
            st.markdown("---")
            st.subheader("読みたい本リスト")
            wishlist_df = get_wishlist(st.session_state.logged_in_user)
            if not wishlist_df.empty:
                for index, row in wishlist_df.iterrows():
                    st.markdown(f"- {row['book_title']}")
            else:
                st.write("読みたい本リストは空です。")
        # ▲▲▲ ここまで ▲▲▲
        
        st.markdown("---")

        # ▼▼▼ 抜けていた検索結果表示部分 ▼▼▼
        if "search_results" in st.session_state and st.session_state.search_results:
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

                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("レビューする", key=f"review_{book['id']}"):
                            st.session_state.selected_book_id = book['id']
                            st.session_state.selected_book_title = book['title']
                            st.rerun()
                    
                    with b_col2:
                        in_wishlist = is_in_wishlist(st.session_state.logged_in_user, book['id'])
                        if st.button("読みたい", key=f"wish_{book['id']}", disabled=in_wishlist):
                            add_to_wishlist(st.session_state.logged_in_user, book['id'], book['title'])
                            st.success(f"「{book['title']}」をリストに追加しました。")
                            st.rerun()
        # ▲▲▲ ここまで ▲▲▲