# 開発環境を段階的に構築する手順

## ステップ1: コアインフラのみ作成 (GitHub不要)

まず、GitHubパイプライン以外のリソースを作成します:

```bash
cd /home/arobet/portfolio/meal_calculate/terraform

# CodePipelineファイルを一時的にリネーム
mv codepipeline.tf codepipeline.tf.disabled

# プランを確認
terraform plan -var-file=terraform.dev.tfvars

# 適用
terraform apply -var-file=terraform.dev.tfvars
```

これで以下が作成されます:
- ECRリポジトリ
- ECSクラスター、タスク定義、サービス
- ALB (Blue/Greenターゲットグループ)
- CodeDeploy設定
- CodeBuild (パイプラインなしで単独実行可能)
- 必要なIAMロール

## ステップ2: 動作確認

### ECR にイメージをプッシュ

```bash
# ECRログイン
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 245775075134.dkr.ecr.us-east-1.amazonaws.com

# イメージをビルド
cd /home/arobet/portfolio/meal_calculate
docker build -t meal-calculate-dev .

# タグ付け
docker tag meal-calculate-dev:latest 245775075134.dkr.ecr.us-east-1.amazonaws.com/meal-calculate-dev:latest

# プッシュ
docker push 245775075134.dkr.ecr.us-east-1.amazonaws.com/meal-calculate-dev:latest
```

### ECSサービスを起動

```bash
# ECSサービスの状態を確認
aws ecs describe-services --cluster meal-calculate-dev-cluster --services meal-calculate-dev-service --region us-east-1

# タスクが起動したら、ALBのDNS名にアクセス
terraform output alb_dns_name
```

## ステップ3: パイプライン追加 (オプション)

動作確認後、GitHubトークンを取得してパイプラインを追加:

```bash
# codepipeline.tfを有効化
mv codepipeline.tf.disabled codepipeline.tf

# terraform.dev.tfvarsにトークンを追加
nano terraform.dev.tfvars

# 再度apply
terraform apply -var-file=terraform.dev.tfvars
```

## クリーンアップ

開発環境が不要になったら:

```bash
cd /home/arobet/portfolio/meal_calculate/terraform
terraform destroy -var-file=terraform.dev.tfvars
```

これで全リソースが削除されます。
