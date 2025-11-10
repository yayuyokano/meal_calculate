# GitHubトークンの更新手順

## エラー内容
```
Could not access the GitHub repository: "meal_calculate". 
The access token might be invalid or has been revoked.
```

## 解決手順

### 1. 新しいGitHub Personal Access Tokenを作成

1. **GitHubにアクセス**: https://github.com/settings/tokens
2. **"Generate new token (classic)"をクリック**
3. **Token名を入力**: 例: `meal-calculate-cicd`
4. **Expiration**: 90 days または No expiration（推奨: 90 days）
5. **必要な権限を選択**:
   - ✅ `repo` - Full control of private repositories
   - ✅ `admin:repo_hook` - Full control of repository hooks
6. **"Generate token"をクリック**
7. **トークンをコピー**（このページを離れると二度と表示されません）

### 2. terraform.tfvarsを更新

```bash
cd /home/arobet/portfolio/meal_calculate/terraform
nano terraform.tfvars
```

以下の行を更新:
```hcl
github_oauth_token = "ghp_your_new_token_here"
```

### 3. Terraformを適用

```bash
# 変更をプレビュー
terraform plan

# パイプラインを更新
terraform apply

# または自動承認で実行
terraform apply -auto-approve
```

### 4. パイプラインの確認

更新後、以下で確認:
```bash
# パイプラインの状態確認
aws codepipeline get-pipeline --name meal-calculate-pipeline --region us-east-1

# パイプラインを手動実行
aws codepipeline start-pipeline-execution \
  --name meal-calculate-pipeline \
  --region us-east-1
```

## トラブルシューティング

### トークンが無効な場合
- トークンの有効期限を確認
- 必要な権限（repo, admin:repo_hook）があるか確認
- リポジトリへのアクセス権限があるか確認

### Webhookエラーの場合
```bash
# 既存のWebhookを削除
terraform destroy -target=aws_codepipeline_webhook.main

# 再作成
terraform apply
```

### パイプライン全体を再作成する場合
```bash
# パイプラインとWebhookを削除
terraform destroy -target=aws_codepipeline_webhook.main -target=aws_codepipeline.main

# 再作成
terraform apply
```

## セキュリティのベストプラクティス

1. **terraform.tfvarsをGitにコミットしない**:
   ```bash
   echo "terraform.tfvars" >> .gitignore
   ```

2. **環境変数を使用**（推奨）:
   ```bash
   export TF_VAR_github_oauth_token="ghp_your_token"
   terraform plan
   ```

3. **AWS Secrets Managerを使用**（本番環境推奨）:
   - トークンをSecrets Managerに保存
   - Terraformから参照するように変更

## 参考リンク

- [GitHub Personal Access Tokens](https://github.com/settings/tokens)
- [CodePipeline GitHub Integration](https://docs.aws.amazon.com/codepipeline/latest/userguide/update-github-action-connections.html)
- [Terraform AWS Provider - CodePipeline](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codepipeline)
