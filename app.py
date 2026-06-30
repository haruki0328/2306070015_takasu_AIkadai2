import streamlit as st
import pandas as pd
from logic import (
    search_books, load_reviews, save_review, increment_like,
    get_ranking_data, register_user, verify_user,
    update_book_status, get_user_books, get_book_status
)

st.set_page_config(page_title="BookShelf Pro", page_icon="📖", layout="wide", initial_sidebar_state="expanded")

if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'app_page' not in st.session_state:
    st.session_state.app_page = "検索"
if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None

# ==========================================
# UIコンポーネント: 本のカード表示
# ==========================================
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

# ==========================================
# メインアプリケーション
# ==========================================
if not st.session_state.logged_in_user:
    # ログイン画面（変更なしのため割愛しますが、先ほどのコードをそのまま使ってください）
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #4A90E2;'>📖 BookShelf Pro</h1>", unsafe_allow_html=True)
        st.write("---")
        if 'auth_mode' not in st.session_state: st.session_state.auth_mode = "ログイン"
        if 'preset_username' not in st.session_state: st.session_state.preset_username = ""

        selected_mode = st.radio(" ", ["ログイン", "新規登録"], index=0 if st.session_state.auth_mode == "ログイン" else 1, horizontal=True, label_visibility="collapsed")
        st.session_state.auth_mode = selected_mode
        
        if st.session_state.auth_mode == "ログイン":
            if 'success_message' in st.session_state:
                st.success(st.session_state.success_message, icon="✅")
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
            st.markdown("<style>.req-box { font-size: 0.85em; color: #555; padding: 10px; background: #f0f2f6; border-radius: 8px; margin-bottom: 15px; }</style>", unsafe_allow_html=True)
            st.markdown(f"<div class='req-box'><b>要件:</b><br>{'✅' if len_ok else '❌'} 8文字以上<br>{'✅' if up_ok else '❌'} 大文字<br>{'✅' if low_ok else '❌'} 小文字<br>{'✅' if num_ok else '❌'} 数字</div>", unsafe_allow_html=True)
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
    # --- サイドバー・ナビゲーション ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state.logged_in_user}")
        st.write("---")
        if st.button("🔍 探索する", use_container_width=True, type="primary" if st.session_state.app_page == "検索" else "secondary"):
            st.session_state.app_page = "検索"; st.session_state.selected_book = None; st.rerun()
        if st.button("📈 トレンド", use_container_width=True, type="primary" if st.session_state.app_page == "ランキング" else "secondary"):
            st.session_state.app_page = "ランキング"; st.session_state.selected_book = None; st.rerun()
        if st.button("📚 本棚ダッシュボード", use_container_width=True, type="primary" if st.session_state.app_page == "マイページ" else "secondary"):
            st.session_state.app_page = "マイページ"; st.session_state.selected_book = None; st.rerun()
        st.write("---")
        if st.button("ログアウト", use_container_width=True):
            st.session_state.clear(); st.rerun()

    # ==========================================
    # 詳細＆レビュー画面 (ステータス管理・AI推薦・いいね機能)
    # ==========================================
    if st.session_state.selected_book:
        book = st.session_state.selected_book
        if st.button("← 戻る"):
            st.session_state.selected_book = None
            st.rerun()
            
        col_img, col_info = st.columns([1, 2])
        with col_img:
            if book.get('cover_url'): st.image(book['cover_url'], use_container_width=True)
            else: st.markdown("<div style='height:300px; display:flex; align-items:center; justify-content:center; background:#f0f2f6; border-radius:10px; color:#888;'>No Image</div>", unsafe_allow_html=True)
            
            # --- 高度な読書ステータス管理 ---
            st.write("---")
            st.markdown("**📚 読書ステータス**")
            current_status = get_book_status(st.session_state.logged_in_user, book['id'])
            status_options = ["未登録", "読みたい", "読書中", "読了"]
            new_status = st.selectbox("状態を選択", status_options, index=status_options.index(current_status), label_visibility="collapsed")
            if st.button("ステータスを更新", use_container_width=True):
                update_book_status(st.session_state.logged_in_user, book['id'], book['title'], book.get('cover_url'), new_status)
                st.toast(f"ステータスを「{new_status}」に更新しました。", icon="✅")
                st.rerun()

        with col_info:
            st.header(book['title'])
            st.caption(f"著者: {book.get('author', '不明な著者')}")
            st.write("---")
            
            st.subheader("📝 レビューを投稿")
            with st.form("review_form", clear_on_submit=True):
                rating = st.slider("評価スコア", 1, 5, 3, format="⭐ %d")
                comment = st.text_area("感想・インサイトを共有")
                if st.form_submit_button("コミュニティに公開"):
                    save_review(book['id'], book['title'], book.get('author', ''), book.get('cover_url'), st.session_state.logged_in_user, rating, comment)
                    st.toast("レビューを公開しました！", icon="✨")
                    st.rerun()

        st.write("---")
        st.subheader("💬 コミュニティのレビュー")
        reviews_df = load_reviews(book['id'])
        if not reviews_df.empty:
            for _, row in reviews_df.iterrows():
                with st.container(border=True):
                    st.markdown(f"**👤 {row['username']}** &nbsp; <span style='color:orange;'>{'★' * int(row['rating'])}</span>", unsafe_allow_html=True)
                    st.write(row['comment'])
                    
                    # SNSライクないいねボタン
                    c1, c2 = st.columns([0.15, 0.85])
                    with c1:
                        if st.button(f"👍 {row['likes']}", key=f"like_{row['review_id']}", help="このレビューにいいねする"):
                            increment_like(row['review_id'])
                            st.rerun()
        else:
            st.info("この本へのレビューはまだありません。")

        # --- 簡易AIリコメンドエンジン（モック） ---
        st.write("---")
        st.subheader("🤖 関連するおすすめ書籍")
        with st.spinner("ネットワークから関連書籍を分析中..."):
            # 著者名を使って動的に検索をかけることでリコメンドを実装
            author_query = book.get('author', '').split(',')[0]
            if author_query and author_query != '不明な著者':
                recommended = search_books(author_query, limit=4)
                # 自分自身を除外
                recommended = [b for b in recommended if b['id'] != book['id']][:4]
                if recommended:
                    cols = st.columns(4)
                    for i, r_book in enumerate(recommended):
                        with cols[i % 4]: render_book_card(r_book)
                else:
                    st.write("関連データが見つかりませんでした。")

    # ==========================================
    # ページ1: 検索
    # ==========================================
    elif st.session_state.app_page == "検索":
        st.title("🔍 探索エンジン")
        query = st.text_input("キーワードを入力", placeholder="技術書、小説、著者名...", label_visibility="collapsed")
        if query:
            with st.spinner("データベースにクエリを送信中..."):
                results = search_books(query)
            if results:
                st.write(f"**{len(results)}** 件のヒット")
                cols = st.columns(4)
                for i, book in enumerate(results):
                    with cols[i % 4]: render_book_card(book)
            else:
                st.warning("条件に一致するレコードがありません。")

    # ==========================================
    # ページ2: ランキング
    # ==========================================
    elif st.session_state.app_page == "ランキング":
        st.title("📈 トレンド＆高評価")
        most_reviewed, top_rated = get_ranking_data()
        col_left, col_right = st.columns(2)
        medals = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}
        
        with col_left:
            st.subheader("🔥 トレンド (レビュー数)")
            if not most_reviewed.empty:
                for idx, row in most_reviewed.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([0.2, 0.8])
                        with c1: st.markdown(f"<h2 style='text-align:center;'>{medals.get(idx+1, '•')}</h2>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"**{row['book_title']}**")
                            st.caption(f"💬 レビュー: {row['review_count']} 件")
                            if st.button("詳細へ", key=f"r1_{row['book_id']}"):
                                st.session_state.selected_book = {"id": row['book_id'], "title": row['book_title'], "author": row['author'], "cover_url": row['cover_url']}
                                st.rerun()
            else: st.info("データがありません。")

        with col_right:
            st.subheader("⭐ トップレーティング")
            if not top_rated.empty:
                for idx, row in top_rated.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([0.2, 0.8])
                        with c1: st.markdown(f"<h2 style='text-align:center;'>{medals.get(idx+1, '•')}</h2>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"**{row['book_title']}**")
                            st.markdown(f"<span style='color:orange;'>★{row['avg_rating']:.1f}</span>", unsafe_allow_html=True)
                            if st.button("詳細へ", key=f"r2_{row['book_id']}"):
                                st.session_state.selected_book = {"id": row['book_id'], "title": row['book_title'], "author": row['author'], "cover_url": row['cover_url']}
                                st.rerun()
            else: st.info("データがありません。")

# ==========================================
    # ページ3: マイページ (本棚ダッシュボード)
    # ==========================================
    elif st.session_state.app_page == "マイページ":
        st.title("📚 本棚ダッシュボード")
        user_books_df = get_user_books(st.session_state.logged_in_user)
        
        # ステータスごとの冊数を集計（エラー回避の安全装置付き）
        count_read = len(user_books_df[user_books_df["status"] == "読了"]) if not user_books_df.empty and "status" in user_books_df.columns else 0
        count_reading = len(user_books_df[user_books_df["status"] == "読書中"]) if not user_books_df.empty and "status" in user_books_df.columns else 0
        count_wish = len(user_books_df[user_books_df["status"] == "読みたい"]) if not user_books_df.empty and "status" in user_books_df.columns else 0

        # ▼▼▼ ここが抜けていました！画面を3列に分割する定義 ▼▼▼
        c1, c2, c3 = st.columns(3)
        
        # メトリクス表示
        c1.metric("読了", f"{count_read} 冊")
        c2.metric("読書中", f"{count_reading} 冊")
        c3.metric("読みたい", f"{count_wish} 冊")
        st.write("---")

        tab1, tab2, tab3 = st.tabs(["✅ 読了", "📖 読書中", "🔖 読みたい"])
        
        def render_bookshelf_grid(df, target_status):
            # dfが空、またはstatus列がない場合は安全に終了させる
            if df.empty or "status" not in df.columns:
                st.info(f"「{target_status}」の本はまだありません。")
                return

            target_books = df[df["status"] == target_status]
            if not target_books.empty:
                cols = st.columns(5) # 5列で本棚のように綺麗に並べる
                for i, (_, row) in enumerate(target_books.iterrows()):
                    with cols[i % 5]:
                        if pd.notna(row['cover_url']):
                            st.image(row['cover_url'], use_container_width=True)
                        else:
                            st.markdown("<div style='height:150px; background:#333; color:white; display:flex; align-items:center; justify-content:center; font-size:12px; text-align:center;'>画像なし</div>", unsafe_allow_html=True)
                        st.caption(row['book_title'][:15])
            else:
                st.info(f"「{target_status}」の本はまだありません。")

        with tab1: render_bookshelf_grid(user_books_df, "読了")
        with tab2: render_bookshelf_grid(user_books_df, "読書中")
        with tab3: render_bookshelf_grid(user_books_df, "読みたい")