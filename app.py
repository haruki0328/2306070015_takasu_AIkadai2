import pandas as pd
import numpy as np

st.title("Uber乗車データ in New York City")

DATE_COLUMN = 'date/time'   # 日時データが入っている列名
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
         'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

@st.cache
def load_date(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)

    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)

    data[DATA_URL] = pd.to_datetime(date[DATE_COLUMN])

    return data
