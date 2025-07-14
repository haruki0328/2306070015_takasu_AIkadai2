# app.py

import streamlit as st
from logic import get_random_joke # logic.pyから関数をインポート

# アプリのタイトル
st.title("ランダムジョーク生成アプリ 😂")

st.write("ボタンを押すと、ランダムな英語のジョークが表示されます。")

# ボタンを作成
if st.button("新しいジョークを取得！"):
    # ボタンが押されたら、ロジック関数を呼び出す
    setup, punchline = get_random_joke()

    if setup and punchline:
        # 成功した場合、結果を表示
        st.subheader("セットアップ (前フリ):")
        st.write(setup)
        st.subheader("パンチライン (オチ):")
        st.write(punchline)
    else:
        # 失敗した場合、エラーメッセージを表示
        st.error("ジョークの取得に失敗しました。もう一度試してください。")