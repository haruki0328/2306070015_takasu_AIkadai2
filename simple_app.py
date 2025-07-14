import streamlit as st

st.title("簡単なStreamlit アプリ")

name = st.text_input("あなたの名前を入力してください")

age = st.slider("年齢を選んでください", 0, 100, 25)

if name:
    st.write(f"こんにちわ、{name}さん！ あなたは{age}歳ですね。")
    st.write(f"{age-5}歳にしか見えないですけど")
else:
    st.write("上の入力欄に名前を入力してください")