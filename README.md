# WBS作成 MCP サーバー

[![Test Suite](https://github.com/tomohirot/mcp-wbs-add2/actions/workflows/test.yml/badge.svg)](https://github.com/tomohirot/mcp-wbs-add2/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/tomohirot/mcp-wbs-add2/branch/main/graph/badge.svg)](https://codecov.io/gh/tomohirot/mcp-wbs-add2)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

プロジェクトマネージャー支援を行う目的で、WBS新規作成/課題追加を行うMCPを作成します。
テンプレート＋新規登録課題を元に一括登録、ミーティングで新たに発生したタスク及び課題/リスクを自動登録する。

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/tomohirot/mcp-wbs-add2.git
cd mcp-wbs-add2

# 仮想環境を作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
make install
# または
pip install -r requirements.txt

# pre-commitフックをインストール
make pre-commit-install
```

### テスト実行

```bash
# 全テストを実行
make test

# カバレッジレポート付きでテスト
make coverage

# カバレッジレポートをブラウザで確認
make coverage-html
```

### 利用可能なコマンド

```bash
make help              # 全コマンドを表示
make test              # テスト実行
make coverage          # カバレッジレポート付きテスト
make lint              # コード品質チェック
make format            # コード自動フォーマット
make type-check        # 型チェック
make clean             # 生成ファイルを削除
make ci-test           # CI パイプライン全体をローカル実行
```

詳細は [CI/CD セットアップガイド](./docs/CI_CD_SETUP.md) を参照してください。

## ☁️ GCPへのデプロイ

### 🚀 クイックデプロイ（推奨）

一括セットアップ＆デプロイスクリプトを使用すると、GCP環境への完全なデプロイが数分で完了します：

```bash
./scripts/setup-and-deploy.sh
```

**このスクリプトが自動実行する内容：**

1. ✅ GCPプロジェクトの設定確認
2. ✅ APIキー等の設定情報を対話的に収集
3. ✅ 必要なGCP APIの有効化
4. ✅ Firestore Databaseの作成
5. ✅ Secret Managerへのシークレット登録
6. ✅ GCSバケットの作成
7. ✅ テストの実行（カバレッジ80%以上）
8. ✅ Cloud Functionsへのデプロイ
9. ✅ デプロイ後の動作確認

**事前準備（以下の情報を手元に用意）：**

- GCP Project ID
- Backlog API Key ([取得方法](https://support-ja.backlog.com/hc/ja/articles/360035641754))
- Backlog Space URL（例：`https://your-space.backlog.com`）
- Notion API Key ([取得方法](https://www.notion.so/my-integrations))

### 手動デプロイ

詳細な制御が必要な場合は、[デプロイガイド](./docs/DEPLOYMENT.md) を参照してください。

### デプロイ後の使い方

```bash
# ヘルスチェック
curl https://YOUR_FUNCTION_URL/health

# WBS作成
curl -X POST https://YOUR_FUNCTION_URL/wbs-create \
  -H 'Content-Type: application/json' \
  -d '{
    "template_url": "https://your-space.backlog.com/view/PROJ-1",
    "project_key": "PROJ"
  }'
```

## 📊 テストカバレッジ

現在のカバレッジ: **94.51%** ✅

**テスト結果:**
- 全263テスト合格 ✅
- カバレッジ 94.51%（目標80%達成）

| モジュール | カバレッジ | 状態 |
|----------|----------|------|
| WBSService | 99% | 🟢 |
| Converter | 97% | 🟢 |
| Validators | 98% | 🟢 |
| BacklogClient | 93% | 🟢 |
| MasterService | 92% | 🟢 |

## 🏗️ アーキテクチャ
        
        - アーキテクチャ
            - 本機能はMCPサーバーとしてテンプレートURLと個別課題を受け付けて動作する。
            - 本体はpythonで記載され、cloud function上で実行される形式とする。
            - 外部との接続はなるべくMCPサーバーを利用する。
                - MCPサーバーはリモート接続が用意されている場合はリモート接続を利用し、Gitでプログラムが提供されている場合はGCP環境に自前のMCPサーバー環境を構築する。
            - 外部サービスとの接続は以下とする。
                - Backlog：backlog mcp
                - Notion：Notion mcp
        - 機能
            - 基本機能
                - URLで渡されたものはURLより外部サービスを判定し、実際の階層を辿り全ファイルデータを取得する。
                - 取得したファイルデータ、もしくはパラメータとして渡されたテキストデータをJSONデータもしくはMarkdownデータへ変換する。
                なお、JSONかMarkdownかはファイル拡張子を元に判断する。
                例)パラメータとして渡されたテキストデータ：Markdown
                　 xlsx：JSON
                    - ファイルデータからテキストデータを抽出する際にはGoogle CloudのDocument AIを利用する
                - 変換したデータからメタデータを保持する。
                    - 取得元ファイル名
                    - 親url
                    - ファイルurl
                    - ファイル名
                    - 更新日
                    - 一からインクリメントしたバージョン番号
                - 生成したメタデータと生成したJSON/Markdownデータをドキュメント保存/検索場所へ保存する。
                    - JSON/MarkdownデータはGCSへ保存
                    - メタデータはgoogle cloud Firestoreへ保存
                - Firestoreから対象ファイルの最新バージョンを検索し、該当するバージョンのデータをGCSから取得する。
            - マスターデータ設定機能
                - 以下を対象プロジェクトから取得
                - プロジェクトデータをチェックし、登録されていないものは登録を行う。
                    - 種別追加：課題、リスク
                    - カテゴリ追加：事前準備、要件定義、基本設計、実装、テスト、リリース、納品
                    - マイルストーン：
                    - カスタム属性：
                        - インプット(文字列)
                        - ゴール/アウトプット(文章)
            - WBS新規作成機能
                - 基本機能を実行する
                - テンプレートのタスクを取得し、新規追加課題とマージする
                    - 新規追加課題はテンプレートタスクのどのカテゴリに当てはまるか判定する。
                    - 判定後テンプレートタスクとマージして一つのタスクリストにする
                - タスクをBacklog MCPを通じてBacklogに登録する。
                その際、プロジェクトのタスク一覧を取得し、未登録のタスクのみを登録すること。
                - 登録結果を保持し、Google Cloud Loggingでログに書き込む。

## ⚠️ 重要な制限事項

**現在のMCP SDK統合はプレースホルダー実装です。**

実際のBacklog/Notion APIと通信するには、以下のファイルで実際のMCP SDK呼び出しを実装する必要があります：
- `src/integrations/backlog/client.py`
- `src/integrations/notion/client.py`

現在は `await asyncio.sleep(0.1)` でモック化されています。本番環境で使用する前に、実際のAPI統合を実装してください。

## 💰 コスト見積もり

月間の推定コスト（中程度の使用量）：

- Cloud Functions: $0-10/月（最初の200万回の呼び出しは無料）
- Firestore: $0-5/月（無料枠: 1GB、50K reads/day）
- Cloud Storage: $0-2/月（最初の5GBは無料）
- Secret Manager: $0.06/secret/月

**合計: 約$1-20/月**

## 🔒 セキュリティ

- ✅ Secret Managerによる認証情報の暗号化保存
- ✅ Cloud Functions Gen 2のセキュリティ機能
- ✅ CORS設定による不正アクセス防止
- ⚠️ 本番環境では `ALLOWED_ORIGINS` を具体的なドメインに設定すること

## 🤝 貢献

Issue、Pull Requestは大歓迎です！

## 📄 ライセンス

MIT License

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
