# logic.py

import requests
import json

# APIからジョークを取得する関数
def get_random_joke():
    """
    JOKE APIにアクセスして、セットアップとパンチラインを含むジョークを返す。
    成功した場合はタプル(setup, punchline)を、失敗した場合は(None, None)を返す。
    """
    api_url = "https://official-joke-api.appspot.com/random_joke"
    try:
        response = requests.get(api_url)
        # ステータスコード200は成功を意味する
        if response.status_code == 200:
            data = response.json()
            setup = data['setup']
            punchline = data['punchline']
            return setup, punchline
        else:
            # APIからエラーが返ってきた場合
            return "ジョークの取得に失敗しました。", f"ステータスコード: {response.status_code}"
    except requests.exceptions.RequestException as e:
        # ネットワークエラーなど
        return "エラーが発生しました。", str(e)