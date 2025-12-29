# Codecov セットアップガイド

カバレッジレポートをCodecovに統合する手順です。

## 📋 前提条件

- GitHubリポジトリが公開されている
- GitHub Actionsが有効
- カバレッジが生成される設定済み（✅ 完了）

## 🚀 セットアップ手順

### 1. Codecovアカウント作成

1. [https://codecov.io](https://codecov.io) にアクセス
2. 「Sign up with GitHub」をクリック
3. GitHubアカウントでログイン
4. 必要な権限を承認

### 2. リポジトリを追加

1. Codecovダッシュボードで「Add a repository」をクリック
2. `tomohirot/mcp-wbs-add2` を検索
3. 「Setup repo」をクリック

### 3. トークンを取得

1. リポジトリ設定画面で「Settings」タブを開く
2. 左メニューから「General」を選択
3. 「Repository Upload Token」セクションでトークンをコピー

**トークン形式例:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 4. GitHubにシークレットを追加

1. GitHubリポジトリページで「Settings」タブを開く
2. 左メニューから「Secrets and variables」 > 「Actions」を選択
3. 「New repository secret」をクリック
4. 以下を入力:
   - **Name**: `CODECOV_TOKEN`
   - **Secret**: （手順3でコピーしたトークン）
5. 「Add secret」をクリック

### 5. 動作確認

1. 新しいコミットをプッシュ（または手動でワークフローを再実行）
   ```bash
   git commit --allow-empty -m "Test Codecov integration"
   git push
   ```

2. GitHub Actionsのログを確認
   - 「Upload coverage reports to Codecov」ステップが成功
   - エラーメッセージがないこと

3. Codecovダッシュボードで確認
   - カバレッジレポートが表示される
   - グラフとトレンドが生成される

## 📊 バッジの追加

セットアップ完了後、READMEにCodecovバッジが表示されます：

```markdown
[![codecov](https://codecov.io/gh/tomohirot/mcp-wbs-add2/branch/main/graph/badge.svg)](https://codecov.io/gh/tomohirot/mcp-wbs-add2)
```

現在のカバレッジ: **80.25%** ✅

## 🔧 トラブルシューティング

### エラー: "Token required"

**原因**: Codecov v4では公開リポジトリでもトークンが必須

**解決策**: 手順4でGitHubシークレットを正しく設定

### エラー: "Could not find a repository"

**原因**: リポジトリがCodecovに追加されていない

**解決策**: 手順2を確認し、リポジトリを追加

### カバレッジが表示されない

**確認項目**:
- GitHub Actionsが成功しているか
- `coverage.xml`ファイルが生成されているか（Artifactsで確認）
- Codecovダッシュボードでアップロード履歴を確認

## 📚 関連リンク

- [Codecov Documentation](https://docs.codecov.com/)
- [GitHub Actions Integration](https://docs.codecov.com/docs/github-actions-integration)
- [本プロジェクトのCI/CD設定](./CI_CD_SETUP.md)

## ⚙️ 現在の設定

ワークフローファイル: `.github/workflows/test.yml`

```yaml
- name: Upload coverage reports to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: false
  env:
    CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
  continue-on-error: true
```

## 📝 注意事項

- `fail_ci_if_error: false` により、Codecovアップロード失敗でもCIは継続
- `continue-on-error: true` により、エラーがあっても後続ステップを実行
- トークンは絶対にコミットしない（GitHubシークレットで管理）

---

**次のステップ**: 手順1-4を実行して、Codecovを有効化してください。
