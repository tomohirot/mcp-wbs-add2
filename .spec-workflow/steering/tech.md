# Technology Stack

## Project Type
このプロジェクトは、MCP（Model Context Protocol）サーバーとして動作するAPIサービスです。Google Cloud Platform上で実行され、プロジェクト管理ツール（BacklogやNotion）との連携を提供します。

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.11+
- **Runtime**: Google Cloud Functions（Python Runtime）
- **Language-specific tools**: pip（パッケージ管理）、venv（仮想環境）

### Key Dependencies/Libraries
- **MCP SDK**: Model Context Protocol サーバー実装のためのSDK
- **Google Cloud Client Libraries**:
  - `google-cloud-documentai`: Document AIによるファイル解析
  - `google-cloud-storage`: GCSへのデータ保存
  - `google-cloud-firestore`: メタデータストレージ
  - `google-cloud-logging`: ログ記録
- **Backlog MCP Client**: Backlogとの連携（リモート接続またはローカル構築）
- **Notion MCP Client**: Notionとの連携（リモート接続またはローカル構築）
- **Requests/httpx**: HTTP通信ライブラリ
- **Pydantic**: データバリデーションとスキーマ定義

### Application Architecture
**MCP Server Architecture（イベント駆動型）**:
- MCPサーバーとして外部からのリクエストを受け付け
- Cloud Functions上でサーバーレス実行
- 外部MCPサーバー（Backlog、Notion）との統合による拡張可能なアーキテクチャ
- Document AI、GCS、Firestoreを活用したデータパイプライン

**処理フロー**:
1. MCPリクエスト受信（URL or テキストデータ）
2. 外部サービス判定とデータ取得（Backlog/Notion MCP経由）
3. Document AIによるファイル解析
4. JSON/Markdownへの変換
5. メタデータ生成とFirestore保存
6. データ本体のGCS保存
7. Backlogへのタスク一括登録
8. Cloud Loggingへの結果記録

### Data Storage
- **Primary storage**:
  - Google Cloud Firestore（メタデータ管理）
  - Google Cloud Storage（JSON/Markdownファイル保存）
- **Caching**: 特になし（Firestoreの最新バージョン検索で実現）
- **Data formats**:
  - JSON（構造化データ、xlsxからの変換結果）
  - Markdown（テキストデータ、議事録など）
  - メタデータスキーマ（取得元ファイル名、親URL、ファイルURL、ファイル名、更新日、バージョン番号）

### External Integrations
- **APIs**:
  - Backlog API（タスク登録、プロジェクト情報取得）
  - Notion API（ページ取得、データベース操作）
  - Google Document AI API（ファイル解析）
- **Protocols**:
  - HTTP/REST（外部API呼び出し）
  - MCP (Model Context Protocol)（MCPサーバー間通信）
  - SSE（Server-Sent Events、MCP Server Protocol）
- **Authentication**:
  - Google Cloud Service Account（GCP サービス認証）
  - API Keys（Backlog、Notion）
  - OAuth 2.0（必要に応じて）

### Monitoring & Dashboard Technologies
- **Dashboard Framework**: Google Cloud Console（ネイティブ管理画面）
- **Real-time Communication**: Google Cloud Logging（ストリームログ）
- **Visualization Libraries**: Cloud Console標準機能
- **State Management**: Firestoreをソースオブトゥルースとして使用

## Development Environment

### Build & Development Tools
- **Build System**: Python標準のsetuptools、またはCloud Functions デプロイツール
- **Package Management**: pip、requirements.txt
- **Development workflow**:
  - ローカル開発: Flask/FastAPIでMCPサーバーをエミュレート
  - Cloud Functionsへのデプロイ: gcloud CLI

### Code Quality Tools
- **Static Analysis**: pylint、mypy（型チェック）
- **Formatting**: black（コードフォーマッター）、isort（import整理）
- **Testing Framework**: pytest（ユニットテスト、統合テスト）
- **Documentation**: Sphinx、docstrings（Google Style）

### Version Control & Collaboration
- **VCS**: Git
- **Branching Strategy**: GitHub Flow（main + feature branches）
- **Code Review Process**: Pull Requestベースのレビュー

### Dashboard Development
- **Live Reload**: Cloud Functions開発時はローカルエミュレータを使用
- **Port Management**: Cloud Functionsはポート自動割り当て
- **Multi-Instance Support**: Cloud Functions のオートスケーリング

## Deployment & Distribution

- **Target Platform(s)**: Google Cloud Platform（Cloud Functions）
- **Distribution Method**: Cloud Functionsへのデプロイ（gcloud CLI）
- **Installation Requirements**:
  - Google Cloud Projectの作成
  - Document AI、GCS、Firestore、Cloud Logging APIの有効化
  - Service Accountの設定と権限付与
  - Backlog/Notion APIキーの取得と設定
- **Update Mechanism**:
  - gcloud functions deploy コマンドによる更新
  - CI/CD（GitHub ActionsまたはCloud Build）

## Technical Requirements & Constraints

### Performance Requirements
- **レスポンス時間**: MCPリクエストから応答まで5秒以内（通常ケース）
- **スループット**: 同時10リクエスト処理可能
- **メモリ使用量**: Cloud Functions 512MB以内
- **Document AI処理時間**: ファイルあたり3秒以内（Google Document AI依存）

### Compatibility Requirements
- **Platform Support**: Google Cloud Platform（Cloud Functions Gen2）
- **Dependency Versions**:
  - Python 3.11以上
  - Google Cloud Client Libraries最新安定版
  - MCP SDK 1.0+
- **Standards Compliance**:
  - MCP (Model Context Protocol) 仕様準拠
  - RESTful API設計原則

### Security & Compliance
- **Security Requirements**:
  - Google Cloud Service Account認証
  - APIキーの環境変数管理（Secret Manager推奨）
  - HTTPS通信の強制
  - GCS/Firestoreのアクセス制御（IAM）
- **Compliance Standards**: 該当なし（プライベート企業利用想定）
- **Threat Model**:
  - APIキー漏洩リスク → Secret Manager使用
  - 不正アクセスリスク → IAMとService Account制限
  - データ漏洩リスク → GCS/Firestoreの暗号化（デフォルト有効）

### Scalability & Reliability
- **Expected Load**: 1日あたり100～500リクエスト（中小規模プロジェクト想定）
- **Availability Requirements**: 99%（Cloud Functions SLAに依存）
- **Growth Projections**:
  - 将来的に複数プロジェクトの同時処理に対応
  - MCPサーバーの水平スケーリング（Cloud Run移行も検討）

## Technical Decisions & Rationale

### Decision Log

1. **Python + Google Cloud Functions**:
   - **選定理由**: Document AIとの統合が容易、サーバーレスで運用コスト削減、Pythonエコシステムの豊富さ
   - **代替案**: Node.js（検討したがPythonのML/AIライブラリとの親和性を優先）

2. **MCP (Model Context Protocol)**:
   - **選定理由**: Backlog/Notionなど複数ツールとの統合を標準化、リモート接続とローカル構築の柔軟性
   - **代替案**: 直接API呼び出し（検討したが拡張性とメンテナンス性でMCPを選択）
   - **トレードオフ**: MCPサーバー構築の初期コスト vs 長期的な拡張性

3. **Firestore + GCS分離アーキテクチャ**:
   - **選定理由**: メタデータ検索（Firestore）とファイル保存（GCS）の責務分離、コスト最適化
   - **代替案**: すべてFirestoreに保存（検討したがストレージコストが高い）
   - **トレードオフ**: 2つのストレージ管理 vs コスト効率

4. **Google Document AI**:
   - **選定理由**: 多様なファイル形式（Excel、PDF、Word等）からの高精度テキスト抽出
   - **代替案**: openpyxl、PyPDF2などのOSSライブラリ（精度と対応形式でDocument AIを選択）
   - **トレードオフ**: APIコスト vs 処理精度と開発工数削減

## Known Limitations

- **Document AI API制限**:
  - **影響**: 月間処理ページ数に上限あり（無料枠1,000ページ/月）
  - **対策**: 大量ファイル処理時は課金またはバッチ処理

- **MCP Server構築の複雑性**:
  - **影響**: Backlog/NotionのGit提供MCPサーバーは自前環境構築が必要
  - **対策**: 初期構築ドキュメント整備、将来的にはDocker化

- **バージョン管理の単純性**:
  - **影響**: インクリメント番号のみでブランチ管理なし
  - **対策**: 必要に応じてGitスタイルのバージョン管理を追加検討

- **エラーハンドリングの堅牢性**:
  - **影響**: 外部API障害時のリトライ機構が未実装
  - **対策**: Cloud Tasksによるリトライキュー実装を検討
