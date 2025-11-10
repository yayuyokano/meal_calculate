# パイプライン条件分岐の実装戦略

## 現在の問題

両方のWebhookが`main`ブランチの全ての変更をトリガーしています:
- アプリ変更 → 両方のパイプラインが実行
- インフラ変更 → 両方のパイプラインが実行

これは無駄なビルドを発生させます。

---

## 解決策1: ブランチ戦略（推奨）

### 設定

**アプリパイプライン**: `main`ブランチをトリガー
```hcl
# codepipeline.tf - 変更なし
filter {
  json_path    = "$.ref"
  match_equals = "refs/heads/main"
}
```

**インフラパイプライン**: `infrastructure`ブランチをトリガー
```hcl
# terraform-pipeline.tf を変更
filter {
  json_path    = "$.ref"
  match_equals = "refs/heads/infrastructure"
}
```

### ワークフロー

```bash
# アプリケーション開発
git checkout main
# コード変更
git push origin main
→ meal-calculate-pipeline のみ実行

# インフラ変更
git checkout infrastructure
# terraform変更
git push origin infrastructure
→ meal-calculate-terraform-pipeline のみ実行

# インフラ変更をmainにマージ
git checkout main
git merge infrastructure
git push origin main
→ アプリパイプラインのみ実行（インフラは変わらない）
```

---

## 解決策2: 手動トリガー（最もシンプル）

Webhookを無効化して、必要な時だけ手動実行:

### アプリデプロイ
```bash
aws codepipeline start-pipeline-execution \
  --name meal-calculate-pipeline \
  --region us-east-1
```

### インフラ更新
```bash
aws codepipeline start-pipeline-execution \
  --name meal-calculate-terraform-pipeline \
  --region us-east-1
```

### Terraform設定
```hcl
# Webhookを削除またはコメントアウト
# resource "aws_codepipeline_webhook" "terraform" {
#   ...
# }
```

---

## 解決策3: GitHub Actionsで制御（最も柔軟）

GitHub Actionsで変更検知してパイプラインを実行:

### .github/workflows/trigger-pipelines.yml
```yaml
name: Trigger AWS Pipelines

on:
  push:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      app_changed: ${{ steps.filter.outputs.app }}
      terraform_changed: ${{ steps.filter.outputs.terraform }}
    steps:
      - uses: actions/checkout@v3
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            app:
              - 'meal_calculate/**'
              - 'Dockerfile'
              - 'requirements.txt'
            terraform:
              - 'terraform/**'

  trigger-app-pipeline:
    needs: detect-changes
    if: needs.detect-changes.outputs.app_changed == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger App Pipeline
        run: |
          aws codepipeline start-pipeline-execution \
            --name meal-calculate-pipeline \
            --region us-east-1
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

  trigger-terraform-pipeline:
    needs: detect-changes
    if: needs.detect-changes.outputs.terraform_changed == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Terraform Pipeline
        run: |
          aws codepipeline start-pipeline-execution \
            --name meal-calculate-terraform-pipeline \
            --region us-east-1
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## 比較表

| 方法 | 複雑さ | 精度 | メンテナンス |
|------|--------|------|-------------|
| ブランチ戦略 | 低 | 高 | 低 |
| 手動トリガー | 最低 | 最高 | なし |
| GitHub Actions | 高 | 最高 | 中 |
| Webhook フィルター | 中 | **低（動作しない）** | 低 |

---

## 推奨アプローチ

### 小規模プロジェクト（現在）
→ **手動トリガー**
- 最もシンプル
- インフラ変更は頻繁ではない
- 確実に制御できる

### 中規模プロジェクト
→ **ブランチ戦略**
- バランスが良い
- Gitフローと統合しやすい

### 大規模プロジェクト
→ **GitHub Actions**
- 最も柔軟
- 他のCI/CDとも統合可能

---

## 実装手順

### 今すぐ実装: 手動トリガーに切り替え

1. Terraform Webhookを無効化:
```bash
cd /home/arobet/portfolio/meal_calculate/terraform
terraform destroy -target=aws_codepipeline_webhook.terraform
```

2. 必要な時だけ手動実行:
```bash
# アプリはWebhookで自動
git push origin main → 自動実行

# インフラは手動
cd terraform
terraform plan  # ローカルで確認
git push origin main  # コードだけpush
aws codepipeline start-pipeline-execution \
  --name meal-calculate-terraform-pipeline  # 手動実行
```

どの方法を実装しますか？
