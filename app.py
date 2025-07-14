import streamlit as st
import pandas as pd     # 表形式データを扱うライブラリ
import numpy as np      # 数値計算のためのライブラリ

# アプリのタイトルを画面に表示
st.title("Uber乗車データ in New York City")

DATE_COLUMN = 'date/time'   # 日時データが入っている列名
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
         'streamlit-demo-data/uber-raw-data-sep14.csv.gz')  # タクシーデータ（表形式）のURL

# データを読み込む関数
@st.cache   #   @st.cache は、一度読み込んだデータを手元に保存しておくことで、2回目以降の読み込みを早くする。
def load_data(nrows):
    
    # データの先頭から nrows行だけ読み込む
    data = pd.read_csv(DATA_URL, nrows=nrows)
    
    # 列名を全て小文字にして、扱いやすくする
    lowercase = lambda x: str(x).lower()    # lambda の書き方はChatGPTに聞いてみてくださいm(_ _)m
    data.rename(lowercase, axis='columns', inplace=True)

    # 日時の列を datetime型に変換する
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    
    return data


data = load_data(15)

st.write(data)