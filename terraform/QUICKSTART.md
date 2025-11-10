# Terraform CI/CD クイックスタート

## 今すぐ始める (3ステップ)

### ステップ1: GitHubにプッシュ

```bash
cd /home/arobet/portfolio/meal_calculate

# 変更を確認
git status

# コミット
git add .
git commit -m "Add Terraform CI/CD automation"
git push
```

### ステップ2: AWSコンソールでCI/CDリソースを確認

#### オプションA: 手動で作成 (簡単)

1. **S3バケット作成**:
   - バケット名: `meal-calculate-terraform-state-245775075134`
   - バージョニング: 有効
   - 暗号化: 有効

2. **DynamoDBテーブル作成**:
   - テーブル名: `meal-calculate-terraform-locks`
   - パーティションキー: `LockID` (文字列)

3. **CodeBuildプロジェクト作成**:
   - プロジェクト名: `meal-calculate-terraform`
   - ソース: CodePipeline
   - Buildspec: `buildspec-terraform.yml`
   - 環境: `aws/codebuild/standard:7.0`

4. **CodePipeline作成**:
   - パイプライン名: `meal-calculate-terraform-pipeline`
   - ソース: GitHub (meal_calculate)
   - ビルド: meal-calculate-terraform
   - 承認ステージを追加
   - デプロイ: なし (CodeBuildで実行)

#### オプションB: Terraformで作成 (推奨)

```bash
cd /home/arobet/portfolio/meal_calculate/terraform

# 既存のファイルを一時的にリネーム (競合回避)
mv terraform-cicd.tf terraform-cicd.tf.disabled
mv terraform-pipeline.tf terraform-pipeline.tf.disabled

# 手動でS3バケットとDynamoDBを作成後...

# ファイルを戻す
mv terraform-cicd.tf.disabled terraform-cicd.tf
mv terraform-pipeline.tf.disabled terraform-pipeline.tf

# 適用
terraform init
terraform apply
```

### ステップ3: テスト実行

```bash
# Terraformファイルを少し変更
cd /home/arobet/portfolio/meal_calculate/terraform
echo "# Test change" >> README.md

# プッシュ
git add .
git commit -m "Test Terraform CI/CD"
git push

# CodePipelineコンソールで確認
# https://console.aws.amazon.com/codesuite/codepipeline/pipelines
```

## デモ: インフラ変更の自動化

### 例1: ECSタスクのCPUを変更

```bash
cd terraform

# ecs.tfを編集
nano ecs.tf
# cpu = "256" を cpu = "512" に変更

git add ecs.tf
git commit -m "Increase ECS task CPU to 512"
git push

# → パイプラインが自動起動
# → terraform planが実行される
# → 承認待ち通知が届く
# → 承認後、terraform applyが実行される
# → CPUが512に変更される
```

### 例2: 新しいターゲットグループを追加

```bash
# alb.tfに新しいターゲットグループを追加
cat >> alb.tf << 'EOF'

resource "aws_lb_target_group" "test" {
  name        = "${var.project_name}-tg-test"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled = true
    path    = "/health"
  }
}
EOF

git add alb.tf
git commit -m "Add test target group"
git push

# → 自動的にリソースが作成される
```

## FAQ

### Q: ローカルでTerraformを実行できる?
A: はい、できます:
```bash
cd terraform
terraform plan
terraform apply
```

### Q: パイプラインをスキップできる?
A: GitHubのコミットメッセージに `[skip ci]` を含めると、パイプラインがスキップされます:
```bash
git commit -m "Update docs [skip ci]"
```

### Q: 承認なしで自動適用できる?
A: セキュリティ上推奨しませんが、terraform-pipeline.tfから承認ステージを削除すれば可能です。

### Q: 複数人で作業する場合は?
A: S3バックエンドとDynamoDBロックにより、安全に協業できます。

## トラブルシューティング

### エラー: "Backend initialization required"

```bash
cd terraform
terraform init
```

### エラー: "Error locking state"

```bash
# 別の実行が完了するまで待つか、強制解除
terraform force-unlock <lock-id>
```

### パイプラインが起動しない

```bash
# Webhookを確認
aws codepipeline list-webhooks --region us-east-1

# 再作成
terraform destroy -target=aws_codepipeline_webhook.terraform
terraform apply
```

## 次のステップ

1. **SNS通知の設定**: メールで承認通知を受け取る
2. **マルチ環境**: dev/staging/prod環境を分離
3. **GitHub Actions統合**: PRでのplan実行
4. **Terraformモジュール化**: 再利用可能なコンポーネント化

おめでとうございます!🎉
Terraformの完全自動化が完成しました!
