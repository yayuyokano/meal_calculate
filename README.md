# Meal Calculator

予算内で最適な学食メニューの組み合わせを見つけるWebアプリケーション

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![AWS ECS](https://img.shields.io/badge/AWS-ECS-orange.svg)](https://aws.amazon.com/ecs/)

## 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [アーキテクチャ](#アーキテクチャ)
- [セットアップ](#セットアップ)
- [使い方](#使い方)
- [デプロイ](#デプロイ)
- [開発](#開発)
- [ライセンス](#ライセンス)

## 概要

Meal Calculatorは、学食のメニューから予算内で最適な組み合わせを自動的に計算するWebアプリケーションです。栄養バランスや好みを考慮しながら、限られた予算で最も満足度の高い食事を提案します。

### デモ

**本番環境**: http://meal-calculate-alb-828374727.us-east-1.elb.amazonaws.com

## 主な機能

- **予算内メニュー計算**: 指定した予算内で最適なメニューの組み合わせを自動計算
- **リアルタイムメニュー取得**: Playwrightを使用して学食の最新メニューを自動取得
- **カテゴリ別選択**: 主菜、副菜、麺類、丼・カレー、デザートなど複数カテゴリから選択
- **動的価格最適化**: 動的計画法を使用した効率的な組み合わせ計算
- **レスポンシブデザイン**: PC・スマートフォン両対応のUI

## 技術スタック

### バックエンド
- **Python 3.11**: プログラミング言語
- **Django 5.0**: Webフレームワーク
- **Gunicorn**: WSGIサーバー
- **Playwright**: Webスクレイピング
- **PostgreSQL**: データベース

### フロントエンド
- **HTML5/CSS3**: マークアップ
- **JavaScript**: インタラクティブ機能
- **Bootstrap** (optional): UIコンポーネント

### インフラ
- **AWS ECS (Fargate)**: コンテナオーケストレーション
- **AWS ECR**: コンテナレジストリ
- **Application Load Balancer**: ロードバランシング
- **AWS RDS**: マネージドデータベース
- **Docker**: コンテナ化

### CI/CD
- **Git**: バージョン管理
- **GitHub**: コードリポジトリ
- **AWS CLI**: デプロイメント

## アーキテクチャ

```
                    ┌─────────────────┐
                    │  Application    │
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   ECS Service   │
                    │   (Fargate)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │  Task 1 │         │  Task 2 │         │  Task N │
   │ Django  │         │ Django  │         │ Django  │
   │ +Gunicorn│        │ +Gunicorn│        │ +Gunicorn│
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                    │
        └───────────────────┼────────────────────┘
                            │
                      ┌─────▼─────┐
                      │  AWS RDS  │
                      │PostgreSQL │
                      └───────────┘
```

## セットアップ

### 前提条件

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL
- AWS CLI (本番環境デプロイ用)

### ローカル開発環境

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd meal_calculate
```

2. **環境変数の設定**
```bash
# .env ファイルを作成
cat > .env << EOF
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/meal_calculate
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
```

3. **依存関係のインストール**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **データベースのマイグレーション**
```bash
cd meal_calculate
python manage.py migrate
python manage.py collectstatic --noinput
```

5. **開発サーバーの起動**
```bash
python manage.py runserver
```

アプリケーションは http://localhost:8000 で利用可能になります。

### Docker Compose での起動

```bash
docker-compose up -d
```

## 使い方

1. **予算の入力**: トップページで食事の予算を入力
2. **カテゴリ選択**: 主菜、副菜などの希望するカテゴリを選択
3. **計算実行**: 「計算」ボタンをクリック
4. **結果確認**: 最適なメニューの組み合わせと合計金額が表示されます

### API使用例

```bash
# JSON形式でリクエスト
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 500,
    "cafeteria": "west2",
    "categories": ["主菜", "副菜"]
  }'
```

## デプロイ

### AWS ECS へのデプロイ

#### 1. ECR にイメージをプッシュ

```bash
# ECR にログイン
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# イメージをビルド
docker build -t meal_calculate:latest .

# タグ付け
docker tag meal_calculate:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/yayuyokano/meal_calculate:latest

# プッシュ
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/yayuyokano/meal_calculate:latest
```

#### 2. ECS サービスの更新

```bash
aws ecs update-service \
  --cluster meal-calculate-cluster \
  --service meal-calculate-service \
  --force-new-deployment \
  --region us-east-1
```

### 環境変数

本番環境では以下の環境変数を ECS タスク定義で設定してください:

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `DEBUG` | デバッグモード | `False` |
| `SECRET_KEY` | Django シークレットキー | `your-secret-key` |
| `DATABASE_URL` | データベース接続URL | `postgresql://...` |
| `ALLOWED_HOSTS` | 許可するホスト | `example.com` |

## 開発

### プロジェクト構造

```
meal_calculate/
├── meal_calculate/           # Djangoアプリケーション
│   ├── calculator/           # メイン計算ロジック
│   │   ├── views.py         # ビュー
│   │   ├── forms.py         # フォーム定義
│   │   ├── urls.py          # URLルーティング
│   │   └── cafeterias.py    # 食堂情報
│   ├── meal_project/        # プロジェクト設定
│   │   ├── settings.py      # Django設定
│   │   ├── urls.py          # ルートURL
│   │   └── wsgi.py          # WSGI設定
│   └── meal_calculator.py   # コア計算アルゴリズム
├── Dockerfile               # Docker設定
├── docker-compose.yml       # Docker Compose設定
├── requirements.txt         # Python依存関係
└── README.md               # このファイル
```

### テストの実行

```bash
cd meal_calculate
python manage.py test
```

### コードスタイル

このプロジェクトは PEP 8 に準拠しています。

```bash
# コードフォーマット
black meal_calculate/

# リンター
flake8 meal_calculate/
```

## トラブルシューティング

### Playwright ブラウザが見つからない

```bash
playwright install chromium
```

### 静的ファイルが表示されない

```bash
python manage.py collectstatic --noinput
```

### データベース接続エラー

`.env` ファイルの `DATABASE_URL` が正しいか確認してください。

## パフォーマンス

- **レスポンスタイム**: 平均 200-500ms
- **スケーラビリティ**: ECS Fargate による自動スケーリング対応
- **可用性**: マルチAZ構成による高可用性

## セキュリティ

- HTTPS 対応 (ALB 経由)
- セキュリティグループによるネットワーク制御
- 環境変数による機密情報管理
- Django のセキュリティベストプラクティスに準拠

## コントリビューション

プルリクエストを歓迎します!大きな変更の場合は、まず Issue を開いて変更内容を議論してください。

## ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています。

## お問い合わせ

質問や提案がある場合は、Issue を作成してください。
