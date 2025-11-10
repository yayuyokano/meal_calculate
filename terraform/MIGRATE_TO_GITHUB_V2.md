# GitHub v2 (CodeStar Connection) への移行

## 現在の問題
GitHub OAuth Token (v1) は非推奨になっており、より安全な CodeStar Connection (v2) への移行が推奨されています。

## 移行手順

### オプション1: AWSコンソールでCodeStar Connectionを作成

1. **AWS CodePipeline Console**: https://console.aws.amazon.com/codesuite/settings/connections
2. **"Create connection"をクリック**
3. **Provider**: GitHub を選択
4. **Connection name**: `meal-calculate-github`
5. **"Connect to GitHub"をクリック**
6. **GitHub認証を完了**
7. **Connection ARNをコピー**

### オプション2: Terraformで作成（推奨）

`codepipeline.tf`に以下を追加:

```hcl
# CodeStar Connection for GitHub
resource "aws_codestarconnections_connection" "github" {
  name          = "${var.project_name}-github"
  provider_type = "GitHub"

  tags = {
    Name    = "${var.project_name}-github-connection"
    Project = var.project_name
  }
}

# 既存のCodePipelineのSource stageを更新
resource "aws_codepipeline" "main" {
  name     = "${var.project_name}-pipeline"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    location = aws_s3_bucket.codepipeline.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"  # Changed from GitHub
      version          = "1"
      output_artifacts = ["SourceArtifact"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github.arn
        FullRepositoryId = "${var.github_repo_owner}/${var.github_repo_name}"
        BranchName       = "main"
        # OutputArtifactFormat = "CODE_ZIP"  # Optional
      }
    }
  }

  # ... 残りのstages ...
}
```

### Terraformで適用

```bash
cd /home/arobet/portfolio/meal_calculate/terraform

# 変更を確認
terraform plan

# 適用
terraform apply
```

### Connection を手動で承認

CodeStar Connectionは作成後、手動で承認が必要です:

```bash
# Connection の状態を確認
aws codestar-connections list-connections --region us-east-1

# AWSコンソールで承認
# https://console.aws.amazon.com/codesuite/settings/connections
# "Pending" 状態の Connection を選択し、"Update pending connection" をクリック
```

## メリット

1. **セキュリティ向上**: Personal Access Tokenより安全
2. **管理が容易**: トークンの期限切れを心配する必要がない
3. **AWS推奨**: GitHub v1 providerは非推奨
4. **細かい権限制御**: リポジトリごとに権限を設定可能

## 比較

| 項目 | GitHub v1 (OAuth) | GitHub v2 (CodeStar) |
|------|-------------------|----------------------|
| セキュリティ | 低 | 高 |
| トークン管理 | 手動 | 自動 |
| AWS推奨 | ❌ 非推奨 | ✅ 推奨 |
| 設定の複雑さ | 簡単 | やや複雑 |

## 今すぐ試す簡易版

現在のトークンエラーを素早く解決したい場合:

1. **新しいトークンを作成**: https://github.com/settings/tokens
2. **terraform.tfvarsを更新**:
   ```bash
   cd /home/arobet/portfolio/meal_calculate/terraform
   nano terraform.tfvars
   # github_oauth_token を更新
   ```
3. **Terraformを再適用**:
   ```bash
   terraform apply -auto-approve
   ```
