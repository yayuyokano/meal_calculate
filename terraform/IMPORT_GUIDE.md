# 既存リソースをTerraform管理下に置く手順

## 重要な注意事項

現在、AWSには既に以下のリソースが存在しています:
- ECRリポジトリ: yayuyokano/meal_calculate
- ECSクラスター: meal-calculate-cluster
- ECSサービス: meal-calculate-service
- ALB: meal-calculate-alb
- ターゲットグループ: meal-calculate-tg, meal-calculate-tg-green
- CodeBuild: meal-calculate-build
- CodePipeline: meal-calculate-pipeline
- CodeDeploy: meal-calculate-app, meal-calculate-dg

これらを`terraform apply`で新規作成しようとすると、既存リソースと競合してエラーになります。

## 2つの選択肢

### オプションA: 既存リソースをインポート (推奨)

既存のリソースをTerraform管理下に置きます。リソースは維持されます。

```bash
# 例: ECRリポジトリをインポート
terraform import aws_ecr_repository.main meal-calculate

# 例: ECSクラスターをインポート
terraform import aws_ecs_cluster.main meal-calculate-cluster
```

**利点**: 既存環境を維持したまま、Terraformで管理開始
**欠点**: すべてのリソースを手動でインポートする必要がある

### オプションB: クリーンな新環境を作成

既存リソースを削除して、Terraformで一から作り直します。

```bash
# 既存リソースを手動削除後
terraform apply
```

**利点**: Terraformで完全に管理された環境
**欠点**: 一時的にサービス停止が発生する

## 推奨アプローチ: ドキュメントとして活用

現時点では、このTerraformコードを以下のように活用することをお勧めします:

1. **ドキュメントとして**: 現在のインフラ構成の明確な記録
2. **別環境構築用**: 開発環境やステージング環境を構築する際に使用
3. **災害復旧用**: 本番環境が壊れた場合の復旧手順として

## 今すぐ試す方法

### 開発環境を別途作成してテスト

```bash
# プロジェクト名を変更して別環境を作成
cd terraform
cp terraform.tfvars terraform.dev.tfvars

# terraform.dev.tfvarsを編集
# project_name = "meal-calculate-dev"

# 開発環境を作成
terraform apply -var-file=terraform.dev.tfvars
```

これで本番環境に影響を与えずにTerraformの動作を確認できます。

## 完全なインポート手順 (参考)

既存リソースをすべてインポートする場合の手順:

```bash
cd terraform

# ECR
terraform import aws_ecr_repository.main meal-calculate

# ECS
terraform import aws_ecs_cluster.main meal-calculate-cluster
terraform import aws_ecs_task_definition.main meal-calculate-task
terraform import aws_ecs_service.main meal-calculate-cluster/meal-calculate-service

# ALB
terraform import aws_lb.main <alb-arn>
terraform import aws_lb_target_group.blue <blue-tg-arn>
terraform import aws_lb_target_group.green <green-tg-arn>
terraform import aws_lb_listener.http <listener-arn>

# CodeDeploy
terraform import aws_codedeploy_app.main meal-calculate-app
terraform import aws_codedeploy_deployment_group.main meal-calculate-app:meal-calculate-dg

# CodeBuild
terraform import aws_codebuild_project.main meal-calculate-build

# CodePipeline
terraform import aws_codepipeline.main meal-calculate-pipeline

# IAMロール
terraform import aws_iam_role.ecs_task_execution_role <role-name>
terraform import aws_iam_role.codedeploy CodeDeployRoleForECS
terraform import aws_iam_role.codebuild codebuild-meal-calculate-build-service-role
terraform import aws_iam_role.codepipeline <codepipeline-role-name>

# S3
terraform import aws_s3_bucket.codepipeline <bucket-name>
```

注意: インポート後、`terraform plan`でdiffが出る場合は、terraform codeを既存リソースの設定に合わせて調整する必要があります。
