# おすすめ本棚アプリ

## アプリ概要

このアプリは、ユーザーが書籍を検索し、レビューを投稿・閲覧できるWebアプリです。
読みたい本リスト（ウィッシュリスト）機能や、レビューランキング表示も備えています。
ユーザー認証機能もあり、個人ごとの履歴管理が可能です。

## 使用API

- [Open Library API](https://openlibrary.org/developers/api)：書籍情報の取得に利用

## システム設計図

外部サービス（Open Library API）との連携や、内部で利用しているCSVファイル（ユーザー・レビュー・ウィッシュリスト管理）との関係を図示しています。

![システム設計図]

## コード説明図

主要なファイル（`app.py`, `logic.py` など）や、主要関数の関係性を図示しています。

![コード説明図]

## ファイル構成

- `app.py`：StreamlitによるUI・画面制御
- `logic.py`：API通信・データ処理・認証ロジック
- `users.csv`：ユーザー情報（ハッシュ化パスワード含む）
- `reviews.csv`：レビュー情報
- `requirements.txt`：必要パッケージ
- `README.md`：この説明書

## 使い方

1. 必要なパッケージをインストール（`pip install -r requirements.txt`）
2. Streamlitで起動（`streamlit run app.py`）
3. Webブラウザでアクセスし、ユーザー登録・ログインして利用

---

## 改善案

- **[夏休み課題の改善案](./improvement.md)**