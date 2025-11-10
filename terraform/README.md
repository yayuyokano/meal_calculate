# Meal Calculate Infrastructure as Code

このディレクトリには、Meal CalculateアプリケーションのAWSインフラをTerraformで管理するコードが含まれています。

## 構成

- **ECS Fargate**: コンテナオーケストレーション
- **Application Load Balancer**: ロードバランサー
- **CodePipeline/CodeBuild/CodeDeploy**: CI/CD パイプライン
- **Blue/Green Deployment**: ゼロダウンタイムデプロイ

## 前提条件

1. Terraform >= 1.0
2. AWS CLI設定済み
3. 既存のVPC、サブネット、セキュリティグループ

## セットアップ

### 1. 変数ファイルの作成

```bash
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars`を編集して、実際の値を設定:

```hcl
# VPC IDを確認
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' --output table

# terraform.tfvarsに記入
vpc_id = "vpc-xxxxx"
subnet_1_id = "subnet-xxxxx"
subnet_2_id = "subnet-xxxxx"
security_group_id = "sg-xxxxx"

# GitHub OAuth token (Personal Access Token)
# https://github.com/settings/tokens
github_oauth_token = "ghp_xxxxx"
github_webhook_secret = "random-secret-string"
```

### 2. Terraform初期化

```bash
cd terraform
terraform init
```

### 3. プランの確認

```bash
terraform plan
```

### 4. インフラのデプロイ

```bash
terraform apply
```

## 使い方

### インフラの状態確認

```bash
terraform show
```

### 特定のリソースを確認

```bash
terraform state list
terraform state show aws_ecs_service.main
```

### 変更の適用

コードを編集後:

```bash
terraform plan
terraform apply
```

### インフラの削除

```bash
terraform destroy
```

## 出力値

デプロイ後、以下の情報が出力されます:

- `alb_dns_name`: ALBのDNS名 (アプリケーションURL)
- `ecr_repository_url`: ECRリポジトリURL
- `codepipeline_name`: CodePipeline名

確認:

```bash
terraform output
```

## 注意事項

- `terraform.tfvars`はGitにコミットしないでください（機密情報を含むため）
- 既に`.gitignore`に追加されています
- 既存のリソースと競合する場合は、`terraform import`で既存リソースをインポート可能

## トラブルシューティング

### 既存リソースとの競合

既存のリソースをインポート:

```bash
# 例: 既存のECRリポジトリをインポート
terraform import aws_ecr_repository.main meal-calculate
```

### ステートファイルの管理

本番環境では、S3バックエンドの使用を推奨:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "meal-calculate/terraform.tfstate"
    region = "us-east-1"
  }
}
```
