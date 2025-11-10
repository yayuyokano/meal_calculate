# パイプライン実行ガイド

## 📋 2つのパイプライン

### 1. meal-calculate-pipeline (アプリケーション) - 🔄 自動実行
**目的**: FastAPIアプリのデプロイ  
**トリガー**: `main`ブランチへのpush（自動）  
**実行時間**: 約5-10分

### 2. meal-calculate-terraform-pipeline (インフラ) - 🖐️ 手動実行
**目的**: AWSインフラの更新  
**トリガー**: 手動実行のみ  
**実行時間**: 約3-5分 + 承認待ち + 2-3分

---

## 🚀 使い方

### アプリケーションをデプロイ（自動）

```bash
# コードを変更
vim meal_calculate/meal_calculate/views.py

# Git push
git add .
git commit -m "Update API endpoint"
git push origin main
```

→ **自動的に**`meal-calculate-pipeline`が実行されます  
→ CloudWatch Logsで進捗確認: https://console.aws.amazon.com/codesuite/codepipeline/pipelines

---

### インフラを更新（手動）

#### ステップ1: ローカルでplanを確認
```bash
cd terraform
terraform plan
```

#### ステップ2: コードをpush
```bash
git add terraform/
git commit -m "Increase ECS task memory"
git push origin main
```

#### ステップ3: パイプラインを手動実行
```bash
aws codepipeline start-pipeline-execution \
  --name meal-calculate-terraform-pipeline \
  --region us-east-1
```

#### ステップ4: 承認メールを待つ
- `reckonyuyo@gmail.com`に通知が届きます
- Planの内容を確認
- AWSコンソールで承認または却下

#### ステップ5: Applyが自動実行
- 承認後、自動的に`terraform apply`が実行されます

---

## 📊 パイプラインの状態確認

### 両方のパイプラインを確認
```bash
aws codepipeline list-pipeline-executions \
  --pipeline-name meal-calculate-pipeline \
  --region us-east-1 \
  --max-items 3
```

```bash
aws codepipeline list-pipeline-executions \
  --pipeline-name meal-calculate-terraform-pipeline \
  --region us-east-1 \
  --max-items 3
```

### 詳細な状態確認
```bash
# アプリパイプライン
aws codepipeline get-pipeline-state \
  --name meal-calculate-pipeline \
  --region us-east-1

# インフラパイプライン
aws codepipeline get-pipeline-state \
  --name meal-calculate-terraform-pipeline \
  --region us-east-1
```

---

## 🔧 よく使うコマンド

### パイプラインの手動実行
```bash
# アプリケーション（通常は自動なので不要）
aws codepipeline start-pipeline-execution \
  --name meal-calculate-pipeline \
  --region us-east-1

# インフラストラクチャ（terraform変更時に使用）
aws codepipeline start-pipeline-execution \
  --name meal-calculate-terraform-pipeline \
  --region us-east-1
```

### パイプラインの停止
```bash
# 実行中のパイプラインを停止
aws codepipeline stop-pipeline-execution \
  --pipeline-name meal-calculate-terraform-pipeline \
  --pipeline-execution-id <execution-id> \
  --reason "Manual stop" \
  --region us-east-1
```

### 承認待ちの一覧
```bash
aws codepipeline list-action-executions \
  --pipeline-name meal-calculate-terraform-pipeline \
  --filter pipelineExecutionId=<execution-id> \
  --region us-east-1
```

---

## 📝 典型的なワークフロー

### シナリオ1: API機能の追加
```bash
# 1. コード変更
vim meal_calculate/meal_calculate/views.py
vim meal_calculate/meal_calculate/forms.py

# 2. ローカルテスト
python manage.py runserver

# 3. Git push
git add meal_calculate/
git commit -m "Add new API endpoint"
git push origin main

# 4. 自動的にデプロイされる（何もしなくてOK）
# 進捗確認: https://console.aws.amazon.com/codesuite/codepipeline/
```

### シナリオ2: ECSのメモリ増設
```bash
# 1. Terraform変更
cd terraform
vim ecs.tf
# memory = "512" → "1024" に変更

# 2. ローカルでplan確認
terraform plan
# 変更内容を確認: +/- リソースの変更

# 3. Git push
git add ecs.tf
git commit -m "Increase ECS task memory to 1024MB"
git push origin main

# 4. パイプラインを手動実行
aws codepipeline start-pipeline-execution \
  --name meal-calculate-terraform-pipeline \
  --region us-east-1

# 5. メールで承認リンクが届く
# → AWSコンソールで承認

# 6. 自動的に apply が実行される
```

### シナリオ3: 緊急バグ修正
```bash
# 1. 素早く修正
vim meal_calculate/meal_calculate/views.py
git add .
git commit -m "Hotfix: Fix critical bug"
git push origin main

# 2. パイプラインの進捗を監視
watch -n 5 'aws codepipeline get-pipeline-state \
  --name meal-calculate-pipeline \
  --region us-east-1 \
  --query "stageStates[*].[stageName,latestExecution.status]" \
  --output table'

# 3. デプロイ完了を確認
curl http://meal-calculate-alb-828374727.us-east-1.elb.amazonaws.com/health
```

---

## ⚠️ 注意事項

### Terraformパイプラインを実行する前に

1. **必ず`terraform plan`を実行**
   ```bash
   cd terraform
   terraform plan
   ```

2. **変更内容を理解する**
   - `+` = 新規作成
   - `~` = 更新
   - `-/+` = 再作成
   - `-` = 削除

3. **破壊的変更に注意**
   - ECSサービスの再作成 → ダウンタイム発生
   - ALBの削除 → サービス停止
   - データベースの削除 → データロス

4. **本番環境では承認を慎重に**
   - Planの内容を詳細に確認
   - 変更のリスクを評価
   - 必要に応じてチームに相談

---

## 🔄 ロールバック

### アプリケーションのロールバック
```bash
# 前のタスク定義に戻す
aws ecs update-service \
  --cluster meal-calculate-cluster \
  --service meal-calculate-service \
  --task-definition meal-calculate-task:9 \
  --region us-east-1
```

### インフラのロールバック
```bash
# Gitで前のコミットに戻す
cd terraform
git log --oneline
git revert <commit-hash>
git push origin main

# パイプラインを実行
aws codepipeline start-pipeline-execution \
  --name meal-calculate-terraform-pipeline \
  --region us-east-1
```

---

## 📞 トラブルシューティング

### パイプラインが失敗した
1. **CloudWatch Logsを確認**
   ```bash
   aws logs tail /aws/codebuild/meal-calculate-build --follow
   ```

2. **エラーメッセージを確認**
   ```bash
   aws codepipeline get-pipeline-execution \
     --pipeline-name meal-calculate-pipeline \
     --pipeline-execution-id <id> \
     --region us-east-1
   ```

### Terraform承認メールが届かない
```bash
# SNS subscriptionを確認
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:245775075134:meal-calculate-terraform-approval \
  --region us-east-1

# メールアドレスの確認を再送
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:245775075134:meal-calculate-terraform-approval \
  --protocol email \
  --notification-endpoint reckonyuyo@gmail.com \
  --region us-east-1
```

---

## 🎯 クイックリファレンス

| アクション | コマンド |
|-----------|---------|
| アプリデプロイ | `git push origin main` (自動) |
| インフラ更新 | `aws codepipeline start-pipeline-execution --name meal-calculate-terraform-pipeline --region us-east-1` |
| 状態確認 | `aws codepipeline get-pipeline-state --name <pipeline-name> --region us-east-1` |
| ログ確認 | `aws logs tail /aws/codebuild/<project-name> --follow` |
| サービス状態 | `curl http://meal-calculate-alb-828374727.us-east-1.elb.amazonaws.com/` |

---

## 📚 関連ドキュメント

- [CICD_SETUP.md](./CICD_SETUP.md) - CI/CDの詳細な設定
- [QUICKSTART.md](./QUICKSTART.md) - クイックスタートガイド
- [PIPELINE_BRANCHING_STRATEGY.md](./PIPELINE_BRANCHING_STRATEGY.md) - パイプライン分岐戦略
- [UPDATE_GITHUB_TOKEN.md](./UPDATE_GITHUB_TOKEN.md) - GitHubトークン更新方法
