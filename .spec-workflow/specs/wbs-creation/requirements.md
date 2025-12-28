# Requirements Document

## Introduction

WBS（Work Breakdown Structure）作成機能は、プロジェクトマネージャーの業務効率化を目的とした機能です。テンプレートURLと新規追加タスクを受け付け、両者をインテリジェントにマージしてBacklogに一括登録します。この機能により、プロジェクト立ち上げ時のタスク登録作業を大幅に削減し、テンプレートの再利用を促進します。

主な価値：
- **時間削減**: 手動タスク登録と比較して80%以上の時間削減
- **品質向上**: テンプレート活用によるタスクの抜け漏れ防止
- **一貫性**: 過去のプロジェクトパターンの再利用による標準化

## Alignment with Product Vision

この機能は、product.mdに記載されたプロダクトビジョンと以下の点で整合します：

1. **自動化ファースト原則**: テンプレート取得、データ変換、タスクマージ、Backlog登録の全プロセスを自動化
2. **柔軟性と拡張性**: MCP経由でBacklog/Notionと連携し、将来的な外部サービス追加が容易
3. **データの透明性**: すべての処理をメタデータとして記録し、トレーサビリティを確保

ビジネス目標への貢献：
- **業務効率化**: プロジェクト立ち上げ時のWBS作成時間を80%削減（目標達成）
- **テンプレート再利用率**: 70%以上の達成に寄与
- **データ整合性**: Backlog登録成功率99%以上を実現

## Requirements

### Requirement 1: テンプレートURLからのデータ取得

**User Story:** プロジェクトマネージャーとして、過去のプロジェクトのWBSテンプレートURLを指定することで、そのタスク構造を再利用したい。これにより、毎回ゼロから作成する手間を省きたい。

#### Acceptance Criteria

1. WHEN ユーザーがBacklogまたはNotionのURLを入力 THEN システムはURLから外部サービスを自動判定する SHALL
2. WHEN URLがBacklogの場合 THEN システムはBacklog MCPクライアント経由でデータを取得する SHALL
3. WHEN URLがNotionの場合 THEN システムはNotion MCPクライアント経由でデータを取得する SHALL
4. WHEN URLから階層データを取得 THEN システムは全ファイル/ページを再帰的に辿る SHALL
5. IF 取得したファイルがExcel形式（.xlsx）の場合 THEN システムはGoogle Document AIを使用してJSONに変換する SHALL
6. IF 取得したファイルがテキスト形式の場合 THEN システムはMarkdown形式として処理する SHALL
7. WHEN データ取得が完了 THEN システムは以下のメタデータを生成してFirestoreに保存する SHALL:
   - 取得元ファイル名
   - 親URL
   - ファイルURL
   - ファイル名
   - 更新日
   - インクリメントしたバージョン番号
8. WHEN メタデータ保存後 THEN システムは変換後のJSON/MarkdownデータをGCSに保存する SHALL
9. WHEN データ取得に失敗した場合 THEN システムはエラーメッセージとともに処理を中断し、Cloud Loggingに記録する SHALL

### Requirement 2: 新規タスクの受付と解析

**User Story:** プロジェクトマネージャーとして、ミーティングで発生した新規タスクをテキストで入力することで、テンプレートに追加したい。これにより、議事録からタスクを手動で抽出する手間を省きたい。

#### Acceptance Criteria

1. WHEN ユーザーが新規タスクをテキストパラメータで渡す THEN システムはテキストをMarkdown形式として受け付ける SHALL
2. WHEN 新規タスクを解析 THEN システムは各タスクのタイトル、説明、優先度、担当者を抽出する SHALL
3. IF 新規タスクにカテゴリ情報が含まれていない場合 THEN システムはタスクの内容からカテゴリを自動判定する SHALL
4. WHEN カテゴリ自動判定を実行 THEN システムは以下のカテゴリから最適なものを選択する SHALL:
   - 事前準備
   - 要件定義
   - 基本設計
   - 実装
   - テスト
   - リリース
   - 納品
5. WHEN 新規タスクの解析が完了 THEN システムはタスクリストを内部形式に変換する SHALL

### Requirement 3: テンプレートタスクと新規タスクのマージ

**User Story:** プロジェクトマネージャーとして、テンプレートタスクと新規タスクが適切にマージされ、一つのタスクリストとして整理されることを期待する。これにより、手動でのマージ作業を省きたい。

#### Acceptance Criteria

1. WHEN テンプレートタスクと新規タスクの両方が準備完了 THEN システムはマージ処理を開始する SHALL
2. WHEN 新規タスクのカテゴリが判定済み THEN システムは同じカテゴリのテンプレートタスクグループに挿入する SHALL
3. IF 新規タスクのカテゴリに対応するテンプレートタスクがない場合 THEN システムは新しいカテゴリグループを作成する SHALL
4. WHEN マージ後 THEN システムはタスクリストをカテゴリ順（事前準備→要件定義→...→納品）にソートする SHALL
5. WHEN 同一カテゴリ内のタスク THEN システムは以下の順序で並べる SHALL:
   - テンプレートタスク（元の順序を維持）
   - 新規タスク（追加順）
6. WHEN マージが完了 THEN システムは統合されたタスクリストを生成する SHALL

### Requirement 4: Backlogへのタスク一括登録

**User Story:** プロジェクトマネージャーとして、マージされたタスクがBacklogに自動的に一括登録されることを期待する。ただし、既存タスクの重複は避けたい。

#### Acceptance Criteria

1. WHEN タスクリストのマージが完了 THEN システムはBacklog MCPクライアント経由でプロジェクトの既存タスク一覧を取得する SHALL
2. WHEN 既存タスク一覧を取得 THEN システムは各タスクのタイトルとキーで重複チェックを行う SHALL
3. IF 登録予定タスクが既存タスクと重複する場合 THEN システムはそのタスクをスキップする SHALL
4. WHEN 未登録タスクのみを抽出 THEN システムはBacklog APIに一括登録リクエストを送信する SHALL
5. WHEN タスク登録時 THEN システムは以下の情報を含める SHALL:
   - タイトル
   - 説明
   - カテゴリ（種別）
   - 優先度
   - 担当者（指定されている場合）
   - カスタム属性（インプット、ゴール/アウトプット）
6. WHEN 登録が成功 THEN システムは登録されたタスクのID、タイトル、URLをレスポンスに含める SHALL
7. WHEN 一部のタスク登録が失敗 THEN システムは成功分と失敗分を分けて結果を返す SHALL
8. WHEN すべての登録処理が完了 THEN システムは登録結果をGoogle Cloud Loggingに記録する SHALL

### Requirement 5: マスターデータの自動設定

**User Story:** プロジェクトマネージャーとして、Backlogプロジェクトに必要なマスターデータ（種別、カテゴリ、マイルストーン）が自動的に設定されることを期待する。これにより、手動設定の手間を省きたい。

#### Acceptance Criteria

1. WHEN WBS作成処理を開始 THEN システムは対象Backlogプロジェクトのマスターデータを取得する SHALL
2. WHEN マスターデータを取得 THEN システムは以下の種別が存在するかチェックする SHALL:
   - 課題
   - リスク
3. IF 必要な種別が存在しない場合 THEN システムは不足している種別を自動追加する SHALL
4. WHEN カテゴリをチェック THEN システムは以下のカテゴリが存在するか確認する SHALL:
   - 事前準備
   - 要件定義
   - 基本設計
   - 実装
   - テスト
   - リリース
   - 納品
5. IF 必要なカテゴリが存在しない場合 THEN システムは不足しているカテゴリを自動追加する SHALL
6. WHEN カスタム属性をチェック THEN システムは以下の属性が存在するか確認する SHALL:
   - インプット（文字列型）
   - ゴール/アウトプット（文章型）
7. IF カスタム属性が存在しない場合 THEN システムは自動作成する SHALL
8. WHEN マスターデータ設定が完了 THEN システムは設定結果をCloud Loggingに記録する SHALL

### Requirement 6: エラーハンドリングとログ記録

**User Story:** システム管理者として、処理の詳細なログと明確なエラーメッセージを確認できることを期待する。これにより、問題発生時の迅速な対応が可能になる。

#### Acceptance Criteria

1. WHEN 任意の処理ステップが開始 THEN システムは処理開始ログをCloud Loggingに記録する SHALL
2. WHEN 外部API呼び出しを実行 THEN システムはリクエストとレスポンスの概要をログに記録する SHALL
3. IF API呼び出しが失敗した場合 THEN システムはエラーレベルのログを記録し、以下を含める SHALL:
   - エラーメッセージ
   - HTTPステータスコード
   - APIエンドポイント
   - リクエストパラメータ（機密情報を除く）
4. WHEN Document AI処理を実行 THEN システムは処理対象ファイル名と処理時間をログに記録する SHALL
5. WHEN FirestoreまたはGCSへの保存を実行 THEN システムは保存先パスとデータサイズをログに記録する SHALL
6. WHEN 処理が正常完了 THEN システムは以下を含む完了ログを記録する SHALL:
   - 処理時間
   - 登録成功タスク数
   - スキップタスク数
   - 生成されたメタデータID
7. WHEN 処理全体が完了またはエラー終了 THEN システムはリクエストIDでトレース可能な構造化ログを出力する SHALL

### Requirement 7: データバージョン管理

**User Story:** プロジェクトマネージャーとして、同じテンプレートURLから複数回WBSを作成した場合、過去のバージョンも参照できることを期待する。これにより、変更履歴の追跡が可能になる。

#### Acceptance Criteria

1. WHEN 同じテンプレートURLから再度データを取得 THEN システムはFirestoreから最新バージョン番号を検索する SHALL
2. WHEN 最新バージョンが存在する場合 THEN システムはバージョン番号をインクリメントする SHALL
3. WHEN 新規データを保存 THEN システムは新しいバージョン番号を付与してGCSに保存する SHALL
4. WHEN ユーザーがバージョン指定なしでデータ取得 THEN システムは最新バージョンのデータを返す SHALL
5. WHEN ユーザーが特定バージョンを指定 THEN システムはFirestoreから該当バージョンのメタデータを検索し、GCSから対応するデータを取得する SHALL
6. WHEN バージョン履歴を参照 THEN システムは同一親URLに紐づくすべてのバージョンをリスト表示する SHALL

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**:
  - `wbs_service.py`: WBS作成のオーケストレーションのみ
  - `task_merger.py`: タスクマージロジックのみ
  - `category_detector.py`: カテゴリ判定ロジックのみ
  - 各モジュールは単一の責務を持つ
- **Modular Design**:
  - `processors/`: データ変換処理を独立モジュール化
  - `integrations/`: 外部サービス連携を独立モジュール化
  - `storage/`: データ永続化を独立モジュール化
- **Dependency Management**:
  - Core層（services）は外部サービス（integrations）に直接依存しない
  - 依存性注入（DI）パターンを使用
  - インターフェース（Pydanticモデル）を介して疎結合を実現
- **Clear Interfaces**:
  - MCPリクエスト/レスポンススキーマを明確に定義
  - サービス間のデータ受け渡しはPydanticモデルを使用
  - 公開APIは`__all__`で明示

### Performance
- **レスポンス時間**:
  - 通常ケース（テンプレート20タスク + 新規5タスク）: 5秒以内
  - Document AI処理: ファイルあたり3秒以内
  - Backlog API一括登録: 50タスクあたり2秒以内
- **スループット**:
  - 同時リクエスト処理: 10リクエスト/秒
  - Cloud Functionsのオートスケーリング活用
- **メモリ使用量**:
  - Cloud Functions 512MB以内
  - 大量データ処理時はストリーミング処理を検討
- **データ取得最適化**:
  - Firestoreクエリはインデックス活用
  - GCSからのデータ取得は必要な範囲のみ

### Security
- **認証**:
  - Google Cloud Service Account認証
  - Backlog/Notion APIキーはSecret Manager管理
- **暗号化**:
  - GCS/Firestoreはデフォルト暗号化（AES-256）
  - API通信はHTTPS強制
- **アクセス制御**:
  - Cloud FunctionsにIAMロール設定
  - GCS/FirestoreにはService Accountの最小権限付与
- **機密情報保護**:
  - APIキー、トークンはログに出力しない
  - エラーメッセージに機密情報を含めない

### Reliability
- **エラーハンドリング**:
  - すべての外部API呼び出しにtry-exceptブロック
  - タイムアウト設定（Backlog API: 30秒、Document AI: 60秒）
- **リトライ機構**:
  - 一時的なAPI障害時は3回までリトライ（指数バックオフ）
  - Cloud Tasksによる非同期リトライキューの検討
- **データ整合性**:
  - Backlog登録成功率99%以上
  - Firestore/GCS保存の原子性保証（トランザクション使用）
- **ロギング**:
  - すべての処理ステップをCloud Loggingに記録
  - リクエストIDによるトレーサビリティ確保

### Usability
- **エラーメッセージ**:
  - ユーザーに分かりやすいエラーメッセージ
  - 「URLが無効です」「Backlog API認証に失敗しました」など具体的な指示
- **進捗フィードバック**:
  - 長時間処理の場合は中間ステータスを返す
  - 「テンプレート取得中...」「タスクマージ中...」「Backlog登録中...」
- **レスポンス形式**:
  - 成功時: 登録されたタスクのID、タイトル、URLのリスト
  - 失敗時: エラーコード、エラーメッセージ、対処方法
- **ドキュメント**:
  - API仕様書（リクエスト/レスポンス形式、エラーコード一覧）
  - セットアップガイド（GCP環境構築、APIキー設定）
