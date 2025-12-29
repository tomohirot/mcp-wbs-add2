# デプロイ前チェックリスト

GCP環境へのデプロイ前に確認すべき項目をまとめたチェックリストです。

## ✅ 事前準備

### 1. アカウント・プロジェクト

- [ ] GCPアカウントを作成済み
- [ ] GCPプロジェクトを作成済み（またはプロジェクトIDを決定）
- [ ] GCPプロジェクトで請求が有効化されている
- [ ] gcloud CLIをインストール済み（`gcloud --version`で確認）
- [ ] gcloud CLIで認証済み（`gcloud auth login`）

### 2. APIキーの取得

- [ ] **Backlog API Key**を取得済み
  - 取得先: Backlog → 個人設定 → API
  - https://support-ja.backlog.com/hc/ja/articles/360035641754
- [ ] **Backlog Space URL**を確認済み（例: `https://your-space.backlog.com`）
- [ ] **Notion API Key**を取得済み
  - 取得先: https://www.notion.so/my-integrations
  - New integrationを作成してInternal Integration Tokenを取得

### 3. ローカル環境

- [ ] Python 3.11+ がインストール済み
- [ ] 仮想環境を作成・有効化済み
- [ ] 依存関係をインストール済み（`pip install -r requirements-dev.txt`）
- [ ] **全テストが合格**（`pytest tests/unit -v`）
- [ ] **カバレッジ80%以上**（`pytest tests/unit --cov=src --cov-fail-under=80`）

## 🚀 デプロイ実行

### 方法1: 一括スクリプト（推奨）

```bash
./scripts/setup-and-deploy.sh
```

**実行前に準備するもの:**
- [ ] GCP Project ID
- [ ] Backlog API Key
- [ ] Backlog Space URL
- [ ] Notion API Key
- [ ] デプロイ先リージョン（デフォルト: asia-northeast1）
- [ ] CORS設定（開発用は`*`、本番用は具体的なドメイン）

### 方法2: 手動デプロイ

詳細は [DEPLOYMENT.md](./DEPLOYMENT.md) 参照

1. [ ] GCP APIの有効化
2. [ ] Firestoreデータベースの作成
3. [ ] Secret Managerへのシークレット登録
4. [ ] GCSバケットの作成
5. [ ] Cloud Functionsのデプロイ

## ✅ デプロイ後の確認

### 1. デプロイ成功確認

```bash
# Function URLを取得
FUNCTION_URL=$(gcloud functions describe wbs-creation-service \
    --gen2 \
    --region=asia-northeast1 \
    --format="value(serviceConfig.uri)")

echo "Function URL: $FUNCTION_URL"
```

- [ ] Function URLが取得できた
- [ ] GCP Consoleでデプロイ状態が「Active」

### 2. ヘルスチェック

```bash
curl $FUNCTION_URL/health
```

**期待されるレスポンス:**
```json
{
  "status": "healthy",
  "server": {
    "name": "wbs-creation-mcp-server",
    "version": "1.0.0",
    "capabilities": {...}
  }
}
```

- [ ] ヘルスチェックが成功（HTTP 200）
- [ ] レスポンスに`"status": "healthy"`が含まれる

### 3. WBS作成テスト

```bash
curl -X POST $FUNCTION_URL/wbs-create \
  -H 'Content-Type: application/json' \
  -d '{
    "template_url": "https://your-space.backlog.com/view/PROJ-1",
    "project_key": "PROJ"
  }'
```

**注意:** 現在はプレースホルダー実装のため、実際のBacklog/Notion APIとは通信しません。

- [ ] HTTPステータス200が返る
- [ ] レスポンスに`"success": true`が含まれる

### 4. ログ確認

```bash
gcloud functions logs read wbs-creation-service \
    --gen2 \
    --region=asia-northeast1 \
    --limit=50
```

- [ ] ログが正常に出力されている
- [ ] エラーログがない（WARNING程度は許容）

## 🔒 セキュリティチェック

### Secret Manager

```bash
# Secretsが正しく作成されているか確認
gcloud secrets list
```

- [ ] `backlog-api-key`が存在する
- [ ] `notion-api-key`が存在する
- [ ] Secretsのバージョンが「enabled」状態

### IAM権限

```bash
# Cloud FunctionのService Accountを確認
gcloud functions describe wbs-creation-service \
    --gen2 \
    --region=asia-northeast1 \
    --format="value(serviceConfig.serviceAccountEmail)"
```

- [ ] Service Accountが適切に設定されている
- [ ] Secret Managerへのアクセス権限がある

### CORS設定

- [ ] 開発環境: `ALLOWED_ORIGINS=*`
- [ ] 本番環境: 具体的なドメインに設定（例: `https://yourdomain.com`）

## 💰 コスト確認

### リソース使用状況

- [ ] GCP Consoleで課金情報を確認
- [ ] 予算アラートを設定（推奨）

**推定コスト（月間）:**
- Cloud Functions: $0-10
- Firestore: $0-5
- Cloud Storage: $0-2
- Secret Manager: ~$0.12（2 secrets）
- **合計: ~$1-20/月**

## ⚠️ 既知の制限事項

### MCP SDK統合（重要）

- [ ] **現在はプレースホルダー実装**であることを理解している
- [ ] 本番利用前に実際のMCP SDK統合が必要なことを理解している
  - `src/integrations/backlog/client.py`
  - `src/integrations/notion/client.py`

### Cloud Functions設定

- [ ] タイムアウト: 540秒（9分）
- [ ] メモリ: 512MB
- [ ] 最大インスタンス数: 10

必要に応じて調整してください。

## 📋 トラブルシューティング

### デプロイ失敗時

1. ログを確認
```bash
gcloud functions logs read wbs-creation-service \
    --gen2 \
    --region=asia-northeast1 \
    --limit=100
```

2. ビルドログを確認
```bash
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

3. Secret Managerの権限確認
```bash
gcloud secrets get-iam-policy backlog-api-key
gcloud secrets get-iam-policy notion-api-key
```

### よくあるエラー

**エラー: "Permission denied"**
- 解決策: `gcloud auth login`で再認証

**エラー: "API not enabled"**
- 解決策: 必要なAPIを有効化
```bash
gcloud services enable API_NAME.googleapis.com
```

**エラー: "Firestore not initialized"**
- 解決策: Firestoreデータベースを作成
```bash
gcloud firestore databases create --location=asia-northeast1
```

## 📞 サポート

問題が解決しない場合:
- GitHub Issues: https://github.com/tomohirot/mcp-wbs-add2/issues
- GCP Support: https://cloud.google.com/support

---

## ✅ 最終確認

全ての項目をチェックした後:

- [ ] デプロイが成功した
- [ ] ヘルスチェックが通った
- [ ] ログにエラーがない
- [ ] セキュリティ設定が適切
- [ ] コストを理解している
- [ ] MCP SDK統合の制限を理解している

**おめでとうございます！デプロイ完了です！🎉**

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
