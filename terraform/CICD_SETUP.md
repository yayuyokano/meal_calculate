# Terraform CI/CD セットアップガイド

## 概要

TerraformコードをGitHubにプッシュすると、自動的にインフラストラクチャの変更が計画・適用されます。

## アーキテクチャ

```
GitHub (terraform/*.tf変更)
  ↓ Webhook
CodePipeline (Terraform専用)
  ↓ Source Stage
CodeBuild (Terraform Plan)
  ↓ Plan Stage
手動承認 (SNS通知)
  ↓ Approval Stage
CodeBuild (Terraform Apply)
  ↓ Apply Stage
インフラ更新完了
```

## セットアップ手順

### ステップ1: バックエンドリソースの作成

まず、Terraform用のCI/CDリソースを作成します:

```bash
cd /home/arobet/portfolio/meal_calculate/terraform

# terraform-cicd.tf と terraform-pipeline.tf を有効化
# (既に作成済み)

# バックエンドリソースを作成
terraform init
terraform plan
terraform apply
```

これで以下が作成されます:
- S3バケット (Terraformステート保存用)
- DynamoDBテーブル (ステートロック用)
- CodeBuildプロジェクト (Terraform実行用)
- CodePipeline (Terraform自動化用)
- SNSトピック (承認通知用)

### ステップ2: バックエンド設定の有効化

ローカルのステートファイルをS3に移行:

```bash
# backend.tf.example を backend.tf にコピー
cp backend.tf.example backend.tf

# S3バケット名を確認
terraform output terraform_state_bucket

# backend.tfのバケット名を更新
nano backend.tf

# ステートをS3に移行
terraform init -migrate-state
```

### ステップ3: SNS通知の設定

承認通知を受け取るメールアドレスを登録:

```bash
# SNSトピックARNを取得
terraform output terraform_approval_topic

# メールアドレスを登録
aws sns subscribe \
  --topic-arn <sns-topic-arn> \
  --protocol email \
  --notification-endpoint your-email@example.com

# 確認メールが届くので承認
```

### ステップ4: GitHubにプッシュ

```bash
cd /home/arobet/portfolio/meal_calculate

# 変更をコミット
git add terraform/
git add buildspec-terraform.yml
git commit -m "Add Terraform CI/CD pipeline"
git push
```

## 使い方

### インフラの変更

1. **Terraformコードを編集**:
   ```bash
   cd /home/arobet/portfolio/meal_calculate/terraform
   nano ecs.tf  # 例: タスクのCPUを変更
   ```

2. **GitHubにプッシュ**:
   ```bash
   git add .
   git commit -m "Update ECS task CPU to 512"
   git push
   ```

3. **自動実行される流れ**:
   - GitHub Webhookがパイプラインをトリガー
   - CodeBuildが`terraform plan`を実行
   - 変更内容がS3に保存される
   - SNS通知が届く (承認待ち)

4. **承認して適用**:
   - CodePipelineコンソールで変更内容を確認
   - 「承認」ボタンをクリック
   - CodeBuildが`terraform apply`を自動実行
   - インフラが更新される

### パイプラインの監視

```bash
# パイプラインの状態を確認
aws codepipeline get-pipeline-state \
  --name meal-calculate-terraform-pipeline \
  --region us-east-1

# 実行履歴を確認
aws codepipeline list-pipeline-executions \
  --pipeline-name meal-calculate-terraform-pipeline \
  --region us-east-1
```

## セキュリティのベストプラクティス

### 1. 承認ゲート
本番環境への変更は必ず手動承認が必要です。

### 2. ステートファイルの保護
- S3バケットは暗号化されています
- バージョニングが有効です
- DynamoDBでステートロックを実装

### 3. IAM権限の最小化
Terraformには必要最小限の権限のみを付与してください。

## トラブルシューティング

### パイプラインが起動しない

```bash
# Webhook設定を確認
aws codepipeline list-webhooks --region us-east-1

# GitHubのWebhook設定を確認
# https://github.com/yayuyokano/meal_calculate/settings/hooks
```

### Terraform Planが失敗する

```bash
# CodeBuildのログを確認
aws codebuild batch-get-builds \
  --ids <build-id> \
  --region us-east-1
```

### ステートロックエラー

```bash
# ロックを強制解除 (注意: 他のユーザーが作業中でないことを確認)
terraform force-unlock <lock-id>
```

## 高度な設定

### 環境ごとのパイプライン

開発環境と本番環境で別々のパイプラインを作成:

```hcl
# terraform.tfvars
project_name = "meal-calculate-prod"

# terraform.dev.tfvars
project_name = "meal-calculate-dev"
```

### プルリクエストでのPlan実行

PRごとに`terraform plan`を実行してレビュー:

```yaml
# .github/workflows/terraform-pr.yml
name: Terraform PR Check
on:
  pull_request:
    paths:
      - 'terraform/**'
jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Terraform Plan
        run: |
          cd terraform
          terraform init
          terraform plan
```

## コスト

CI/CDリソースの月額コスト目安:
- S3 (ステートファイル): $0.01 未満
- DynamoDB (ステートロック): $0.25 未満
- CodePipeline: $1.00/月
- CodeBuild: 実行時のみ ($0.005/分)
- SNS: 通知数に応じて

**合計: 約 $1.50/月**

## まとめ

これで、Terraformの変更をGitにプッシュするだけで、安全にインフラを更新できるようになりました!

- ✅ 自動化されたインフラ更新
- ✅ 変更の可視化 (terraform plan)
- ✅ 承認ゲート (本番保護)
- ✅ 履歴管理 (Gitとステートファイル)
- ✅ チーム協業対応 (ステートロック)
