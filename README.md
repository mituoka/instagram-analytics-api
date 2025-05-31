<div align="center">

# Instagram Analytics API

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

インフルエンサーの Instagram データを分析するための RESTful API

</div>

## 📋 目次

- [プロジェクト概要](#-プロジェクト概要)
- [機能一覧](#-機能一覧)
- [技術スタック](#-技術スタック)
- [開発環境のセットアップ](#-開発環境のセットアップ)
- [使い方・API エンドポイント](#-使い方apiエンドポイント)
- [プロジェクト構成](#-プロジェクト構成)
- [ライセンス](#-ライセンス)

## 📝 プロジェクト概要

この API は、インフルエンサーの Instagram 投稿データを収集・分析し、統計情報を提供するサービスです。平均いいね数やコメント数などの指標に基づくランキングや、各インフルエンサーの詳細な統計情報を取得できます。マーケティング分析や影響力のあるインフルエンサーの発見に役立つツールです。

## ✨ 機能一覧

- **インフルエンサーランキング**
  - 平均いいね数の多い順でのランキング
  - 平均コメント数の多い順でのランキング
- **テキスト分析**
  - インフルエンサーの投稿から頻出キーワードを抽出

## 🛠️ 技術スタック

| カテゴリ             | 技術                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------- |
| **フレームワーク**   | [FastAPI](https://fastapi.tiangolo.com/)                                              |
| **データベース**     | [PostgreSQL](https://www.postgresql.org/)                                             |
| **ORM**              | [SQLAlchemy](https://www.sqlalchemy.org/)                                             |
| **コンテナ化**       | [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/) |
| **マイグレーション** | [Alembic](https://alembic.sqlalchemy.org/)                                            |
| **テキスト分析**     | [Janome](https://mocobeta.github.io/janome/)                                          |
| **テスト**           | [pytest](https://pytest.org/)                                                         |

## 🚀 開発環境のセットアップ

### 📋 前提条件

- Docker: 20.10.0 以上
- Docker Compose: 2.0.0 以上
- Python: 3.11 以上

### 🐳 Docker 環境での構築と実行

#### 1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/instagram-analytics-api.git
cd instagram-analytics-api
```

#### 2. 環境変数の設定（オプション）

`.env.example`をコピーして`.env`ファイルを作成し、必要に応じて環境変数を変更します。

```bash
cp .env.example .env
# 必要に応じて.envファイルを編集
```

#### 3. コンテナのビルドと起動

```bash
# コンテナを起動
docker-compose up -d
```

#### 4. データのインポート

独自の CSV ファイルからデータをインポートできます。以下の手順でデータをインポートしてください。

1. まず、あなたの CSV ファイルをプロジェクトの`data`ディレクトリに配置します。
2. 次に、Docker コンテナを使って CSV データをインポートします。

```bash
# 配置したCSVファイルをデータベースにインポート
docker-compose exec app python -m cli.import_csv --file /app/data/your_data.csv
```

CSV ファイルは以下のカラムを含む必要があります。

| カラム名        | 型     | 説明                                 | 例                              |
| --------------- | ------ | ------------------------------------ | ------------------------------- |
| `influencer_id` | 整数   | インフルエンサーを識別する ID        | `1`                             |
| `post_id`       | 整数   | 投稿を識別する ID                    | `2683533358935178826`           |
| `shortcode`     | 文字列 | Instagram 投稿のショートコード       | `CU90186Pf5K`                   |
| `likes`         | 整数   | 投稿のいいね数                       | `140967`                        |
| `comments`      | 整数   | 投稿のコメント数                     | `2217`                          |
| `thumbnail`     | 文字列 | サムネイル画像の URL（任意）         | `https://example.com/image.jpg` |
| `text`          | 文字列 | 投稿のテキスト内容（任意）           | `投稿テキストの例...`           |
| `post_date`     | 日時   | 投稿日時（YYYY-MM-DD HH:MM:SS 形式） | `2021-10-13 19:48:46`           |

#### 5. API の動作確認

### 🐙 Docker 環境の構成

本プロジェクトは以下のコンテナで構成されています。

| コンテナ | 説明                     | 設定                                                                                                                         |
| -------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **app**  | FastAPI アプリケーション | • イメージ: `python:3.11-slim`<br>• ポート: `8000`<br>• コード変更を即時反映                                                 |
| **db**   | PostgreSQL データベース  | • イメージ: `postgres:15`<br>• ポート: `5432`<br>• データ永続化: `postgres_data`ボリューム<br>• 初期化: `init.sql`で自動構築 |

## 📘 使い方・API エンドポイント

API は `http://localhost:8000` で利用可能です。  
Swagger UI ドキュメントは `http://localhost:8000/docs` で確認できます。

### 🔍 API 一覧

| エンドポイント                               | メソッド | 説明                             | パラメータ                                                                 |
| -------------------------------------------- | -------- | -------------------------------- | -------------------------------------------------------------------------- |
| `/api/v1/influencers/ranking/likes`          | GET      | いいね数ランキング               | `limit`: 取得件数（1-100）                                                 |
| `/api/v1/influencers/ranking/comments`       | GET      | コメント数ランキング             | `limit`: 取得件数（1-100）                                                 |
| `/api/v1/analytics/{influencer_id}/keywords` | GET      | インフルエンサーの頻出キーワード | `influencer_id`: インフルエンサー ID<br>`limit`: 取得キーワード数（1-100） |

### 📈 いいね数ランキング API

平均いいね数の多い順にインフルエンサーをランキングします。

#### リクエスト

```http
GET /api/v1/influencers/ranking/likes?limit=5
```

#### レスポンス例

```json
[
  {
    "influencer_id": 71,
    "avg_value": 134994.83,
    "total_posts": 24
  },
  {
    "influencer_id": 1,
    "avg_value": 119515.75,
    "total_posts": 24
  }
  // ...他のインフルエンサー
]
```

### 📊 コメント数ランキング API

平均コメント数の多い順にインフルエンサーをランキングします。

#### リクエスト

```http
GET /api/v1/influencers/ranking/comments?limit=5
```

#### レスポンス例

```json
[
  {
    "influencer_id": 1,
    "avg_value": 1586.08,
    "total_posts": 24
  },
  {
    "influencer_id": 71,
    "avg_value": 310.83,
    "total_posts": 24
  }
  // ...他のインフルエンサー
]
```

### 📊 インフルエンサーの頻出キーワード分析 API

指定されたインフルエンサーの投稿テキストから、頻出する名詞を抽出します。Janome 形態素解析エンジンを使用した日本語テキスト分析に対応しています。

#### リクエスト

```http
GET /api/v1/analytics/{influencer_id}/keywords?limit=10
```

#### レスポンス例

```json
{
  "keywords": [
    {
      "word": "さん",
      "count": 16
    },
    {
      "word": "是非",
      "count": 12
    },
    {
      "word": "洋服",
      "count": 8
    }
    // ...他のキーワード
  ],
  "total_analyzed_posts": 48
}
```

## 📁 プロジェクト構成

```
instagram-analytics-api/
├── alembic/                 # マイグレーションスクリプト
├── app/
│   ├── database/            # データベース接続設定
│   ├── models/              # データモデルとスキーマ
│   ├── routers/             # APIルーター
│   ├── services/            # ビジネスロジック
│   └── main.py              # アプリケーションエントリーポイント
├── cli/                     # コマンドラインツール
├── data/                    # サンプルデータ
├── docker/                  # Dockerファイル
├── tests/                   # テストコード
├── docker-compose.yml       # Docker Compose設定
└── requirements.txt         # 依存パッケージ
```

## 🧪 テストの実行方法

このプロジェクトでは単体テスト、統合テスト、カバレッジレポート生成をサポートしています。

### Docker 環境でのテスト実行

Docker 環境では、以下のコマンドでテストを実行できます：

```bash
docker exec instagram-analytics-api-app-1 pytest --cov --cov-report=xml --cov-report=term
```

## 📄 ライセンス

このプロジェクトは[MIT ライセンス](LICENSE)の下で公開されています。
