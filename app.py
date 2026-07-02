import streamlit as st
import pandas as pd
from logic import (
    search_books, load_reviews, save_review, increment_like,
    get_ranking_data, register_user, verify_user,
    update_book_status, get_user_books, get_book_status,
    get_random_books
)

st.set_page_config(page_title="BookShelf Pro", layout="wide", initial_sidebar_state="expanded")

if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'app_page' not in st.session_state:
    st.session_state.app_page = "検索"
if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None
if 'liked_reviews' not in st.session_state:
    st.session_state.liked_reviews = set()


def render_book_card(book):
    with st.container(border=True):
        if book.get("cover_url"):
            st.image(book["cover_url"], use_container_width=True)
        else:
            st.markdown("<div style='height:200px; display:flex; align-items:center; justify-content:center; background:#f0f2f6; border-radius:5px; margin-bottom:10px; color:#888;'>画像なし</div>", unsafe_allow_html=True)

        st.markdown(f"**{book['title'][:25]}**")

        if st.button("詳細・レビュー", key=f"btn_{book['id']}", use_container_width=True):
            st.session_state.selected_book = book
            st.rerun()

if not st.session_state.logged_in_user:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #4A90E2;'>BookShelf Pro</h1>", unsafe_allow_html=True)
        st.write("---")

        if 'auth_mode' not in st.session_state:
            st.session_state.auth_mode = "ログイン"
        if 'preset_username' not in st.session_state:
            st.session_state.preset_username = ""

        selected_mode = st.radio(" ", ["ログイン", "新規登録"], index=0 if st.session_state.auth_mode == "ログイン" else 1, horizontal=True, label_visibility="collapsed")
        st.session_state.auth_mode = selected_mode

        if st.session_state.auth_mode == "ログイン":
            if 'success_message' in st.session_state:
                st.success(st.session_state.success_message)
                del st.session_state.success_message

            with st.form("login_form"):
                username = st.text_input("ユーザー名", value=st.session_state.preset_username)
                password = st.text_input("パスワード", type="password")
                if st.form_submit_button("ログイン", use_container_width=True):
                    if verify_user(username, password):
                        st.session_state.logged_in_user = username
                        st.session_state.preset_username = ""
                        st.rerun()
                    else:
                        st.error("認証失敗: ユーザー名またはパスワードが間違っています。")

        elif st.session_state.auth_mode == "新規登録":
            new_username = st.text_input("ユーザー名", key="reg_user")
            new_password = st.text_input("パスワード", type="password", key="reg_pass")

            len_ok = len(new_password) >= 8
            up_ok = any(c.isupper() for c in new_password)
            low_ok = any(c.islower() for c in new_password)
            num_ok = any(c.isdigit() for c in new_password)

            st.markdown("""
                <style>
                .req-box { padding: 10px 10px 4px; background: #f0f2f6; border-radius: 8px; margin-bottom: 15px; }
                .req-item { display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; margin: 0 6px 6px 0; }
                .req-ok { background: #e6f4ea; color: #1e7e34; }
                .req-ng { background: #f0f0f0; color: #888; }
                </style>
            """, unsafe_allow_html=True)
            requirements = [(len_ok, "8文字以上"), (up_ok, "大文字"), (low_ok, "小文字"), (num_ok, "数字")]
            items_html = "".join(
                f"<span class='req-item {'req-ok' if ok else 'req-ng'}'>{'✓' if ok else '○'} {label}</span>"
                for ok, label in requirements
            )
            st.markdown(f"<div class='req-box'>{items_html}</div>", unsafe_allow_html=True)

            if st.button("アカウントを作成", use_container_width=True, type="primary"):
                if not (len_ok and up_ok and low_ok and num_ok):
                    st.error("セキュリティ要件を満たしていません。")
                else:
                    success, msg = register_user(new_username, new_password)
                    if success:
                        st.session_state.auth_mode = "ログイン"
                        st.session_state.preset_username = new_username
                        st.session_state.success_message = msg
                        st.rerun()
                    else:
                        st.error(msg)

else:
    with st.sidebar:
        st.markdown(f"### {st.session_state.logged_in_user}")
        st.write("---")
        if st.button("検索", use_container_width=True, type="primary" if st.session_state.app_page == "検索" else "secondary"):
            st.session_state.app_page = "検索"
            st.session_state.selected_book = None
            st.rerun()
        if st.button("トレンド", use_container_width=True, type="primary" if st.session_state.app_page == "ランキング" else "secondary"):
            st.session_state.app_page = "ランキング"
            st.session_state.selected_book = None
            st.rerun()
        if st.button("本棚", use_container_width=True, type="primary" if st.session_state.app_page == "マイページ" else "secondary"):
            st.session_state.app_page = "マイページ"
            st.session_state.selected_book = None
            st.rerun()
        st.write("---")
        if st.button("ログアウト", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if st.session_state.selected_book:
        book = st.session_state.selected_book
        if st.button("← 戻る"):
            st.session_state.selected_book = None
            st.rerun()

        col_img, col_info = st.columns([1, 2])

        with col_img:
            if book.get('cover_url'):
                st.image(book['cover_url'], use_container_width=True)
            else:
                st.markdown("<div style='height:300px; display:flex; align-items:center; justify-content:center; background:#f0f2f6; border-radius:10px; color:#888;'>No Image</div>", unsafe_allow_html=True)

            st.write("---")
            st.markdown("**読書ステータス**")

            current_status = get_book_status(st.session_state.logged_in_user, book['id'])
            status_options = ["未登録", "読みたい", "読書中", "読了"]
            new_status = st.selectbox("状態を選択", status_options, index=status_options.index(current_status), label_visibility="collapsed")

            if st.button("ステータスを更新", use_container_width=True):
                update_book_status(st.session_state.logged_in_user, book['id'], book['title'], book.get('cover_url'), new_status)
                st.toast(f"ステータスを「{new_status}」に更新しました。")
                st.rerun()

        with col_info:
            st.header(book['title'])
            st.caption(f"著者: {book.get('author', '不明な著者')}")
            st.write("---")

            st.subheader("レビュー投稿")
            with st.form("review_form", clear_on_submit=True):
                rating = st.slider("評価スコア", 1, 5, 3)
                comment = st.text_area("感想を共有")
                if st.form_submit_button("投稿する"):
                    save_review(book['id'], book['title'], book.get('author', ''), book.get('cover_url'), st.session_state.logged_in_user, rating, comment)
                    st.toast("レビューを投稿しました")
                    st.rerun()

        st.write("---")
        st.subheader("コミュニティのレビュー")
        reviews_df = load_reviews(book['id'])
        if not reviews_df.empty:
            for _, row in reviews_df.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['username']}** &nbsp; <span style='color:orange;'>{'★' * int(row['rating'])}</span>", unsafe_allow_html=True)
                    if row['comment']:
                        st.write(row['comment'])
                    else:
                        st.caption("（コメントなし）")

                    already_liked = row['review_id'] in st.session_state.liked_reviews
                    c1, c2 = st.columns([0.15, 0.85])
                    with c1:
                        if st.button(
                            f"{'❤️' if already_liked else '🤍'} {row['likes']}",
                            key=f"like_{row['review_id']}",
                            help="いいね済みです" if already_liked else "このレビューにいいねする",
                            disabled=already_liked,
                        ):
                            increment_like(row['review_id'])
                            st.session_state.liked_reviews.add(row['review_id'])
                            st.rerun()
        else:
            st.info("この本へのレビューはまだありません。")

        st.write("---")
        st.subheader("関連する書籍")
        with st.spinner("関連書籍を検索中..."):
            author_query = book.get('author', '').split(',')[0]
            if author_query and author_query != '不明な著者':
                recommended = search_books(author_query, limit=4)
                recommended = [b for b in recommended if b['id'] != book['id']][:4]

                if recommended:
                    cols = st.columns(4)
                    for i, r_book in enumerate(recommended):
                        with cols[i % 4]:
                            render_book_card(r_book)
                else:
                    st.write("関連データが見つかりませんでした。")

    elif st.session_state.app_page == "検索":
        st.title("検索")
        col_q, col_btn = st.columns([5, 1])
        with col_q:
            query = st.text_input("キーワードを入力", placeholder="技術書、小説、著者名...", label_visibility="collapsed")
        with col_btn:
            shuffle_clicked = st.button("シャッフル", use_container_width=True)

        if query:
            with st.spinner("検索中..."):
                results = search_books(query)

            if results:
                st.write(f"**{len(results)}** 件のヒット")
                cols = st.columns(4)
                for i, book in enumerate(results):
                    with cols[i % 4]:
                        render_book_card(book)
            else:
                st.warning("指定されたキーワードでは見つかりませんでした。")
                st.markdown("##### こちらはいかがですか？")
                random_books = get_random_books()
                if random_books:
                    cols = st.columns(4)
                    for i, book in enumerate(random_books):
                        with cols[i % 4]:
                            render_book_card(book)
        else:
            if shuffle_clicked:
                get_random_books.clear()
            st.markdown("##### 今日のおすすめ")
            random_books = get_random_books()
            if random_books:
                cols = st.columns(4)
                for i, book in enumerate(random_books):
                    with cols[i % 4]:
                        render_book_card(book)
            else:
                st.info("データが取得できませんでした。")

    elif st.session_state.app_page == "ランキング":
        st.title("トレンド＆高評価")
        most_reviewed, top_rated = get_ranking_data()
        col_left, col_right = st.columns(2)
        medals = {1: "1位", 2: "2位", 3: "3位", 4: "4位", 5: "5位"}

        with col_left:
            st.subheader("トレンド (レビュー数)")
            if not most_reviewed.empty:
                for idx, row in most_reviewed.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([0.2, 0.8])
                        with c1:
                            st.markdown(f"<h3 style='text-align:center;'>{medals.get(idx+1, '-')}</h3>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"**{row['book_title']}**")
                            st.caption(f"レビュー: {row['review_count']} 件")
                            if st.button("詳細へ", key=f"r1_{row['book_id']}"):
                                st.session_state.selected_book = {"id": row['book_id'], "title": row['book_title'], "author": row['author'], "cover_url": row['cover_url']}
                                st.rerun()
            else:
                st.info("データがありません。")

        with col_right:
            st.subheader("トップレーティング")
            if not top_rated.empty:
                for idx, row in top_rated.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([0.2, 0.8])
                        with c1:
                            st.markdown(f"<h3 style='text-align:center;'>{medals.get(idx+1, '-')}</h3>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"**{row['book_title']}**")
                            st.markdown(f"<span style='color:orange;'>★{row['avg_rating']:.1f}</span>", unsafe_allow_html=True)
                            if st.button("詳細へ", key=f"r2_{row['book_id']}"):
                                st.session_state.selected_book = {"id": row['book_id'], "title": row['book_title'], "author": row['author'], "cover_url": row['cover_url']}
                                st.rerun()
            else:
                st.info("データがありません。")

    elif st.session_state.app_page == "マイページ":
        st.title("本棚ダッシュボード")
        user_books_df = get_user_books(st.session_state.logged_in_user)

        has_status_col = not user_books_df.empty and "status" in user_books_df.columns
        count_read = len(user_books_df[user_books_df["status"] == "読了"]) if has_status_col else 0
        count_reading = len(user_books_df[user_books_df["status"] == "読書中"]) if has_status_col else 0
        count_wish = len(user_books_df[user_books_df["status"] == "読みたい"]) if has_status_col else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("読了", f"{count_read} 冊")
        c2.metric("読書中", f"{count_reading} 冊")
        c3.metric("読みたい", f"{count_wish} 冊")
        st.write("---")

        tab1, tab2, tab3 = st.tabs(["読了", "読書中", "読みたい"])

        def render_bookshelf_grid(df, target_status):
            if df.empty or "status" not in df.columns:
                st.info(f"「{target_status}」に登録されている本はありません。")
                return

            target_books = df[df["status"] == target_status]
            if not target_books.empty:
                cols = st.columns(5)
                for i, (_, row) in enumerate(target_books.iterrows()):
                    with cols[i % 5]:
                        if pd.notna(row['cover_url']):
                            st.image(row['cover_url'], use_container_width=True)
                        else:
                            st.markdown("<div style='height:150px; background:#333; color:white; display:flex; align-items:center; justify-content:center; font-size:12px; text-align:center;'>画像なし</div>", unsafe_allow_html=True)
                        st.caption(row['book_title'][:15] + "..." if len(row['book_title']) > 15 else row['book_title'])
            else:
                st.info(f"「{target_status}」に登録されている本はありません。")

        with tab1:
            render_bookshelf_grid(user_books_df, "読了")
        with tab2:
            render_bookshelf_grid(user_books_df, "読書中")
        with tab3:
            render_bookshelf_grid(user_books_df, "読みたい")
