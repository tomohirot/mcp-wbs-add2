# Project Structure

## Directory Organization

```
mcp-wbs-add2/
├── src/                        # メインソースコード
│   ├── main.py                # Cloud Functions エントリーポイント
│   ├── mcp/                   # MCPサーバー実装
│   │   ├── __init__.py
│   │   ├── server.py          # MCPサーバー本体
│   │   ├── handlers.py        # リクエストハンドラー
│   │   └── schemas.py         # MCPリクエスト/レスポンススキーマ
│   ├── services/              # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── wbs_service.py     # WBS新規作成サービス
│   │   ├── master_service.py  # マスターデータ設定サービス
│   │   ├── task_merger.py     # タスクマージロジック
│   │   └── category_detector.py # カテゴリ判定ロジック
│   ├── integrations/          # 外部サービス連携
│   │   ├── __init__.py
│   │   ├── backlog/
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # Backlog MCPクライアント
│   │   │   └── models.py      # Backlogデータモデル
│   │   ├── notion/
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # Notion MCPクライアント
│   │   │   └── models.py      # Notionデータモデル
│   │   └── mcp_factory.py     # MCPクライアントファクトリ
│   ├── processors/            # データ処理
│   │   ├── __init__.py
│   │   ├── document_processor.py # Document AI統合
│   │   ├── converter.py       # JSON/Markdown変換
│   │   └── url_parser.py      # URL解析とサービス判定
│   ├── storage/               # データ永続化
│   │   ├── __init__.py
│   │   ├── gcs_client.py      # GCSクライアント
│   │   ├── firestore_client.py # Firestoreクライアント
│   │   └── metadata.py        # メタデータモデル
│   ├── utils/                 # ユーティリティ
│   │   ├── __init__.py
│   │   ├── logger.py          # Cloud Loggingラッパー
│   │   ├── config.py          # 設定管理
│   │   └── validators.py      # バリデーション
│   └── models/                # データモデル
│       ├── __init__.py
│       ├── task.py            # タスクモデル
│       ├── metadata.py        # メタデータモデル
│       └── enums.py           # 列挙型定義
├── tests/                     # テストコード
│   ├── unit/                  # ユニットテスト
│   │   ├── test_services/
│   │   ├── test_processors/
│   │   ├── test_integrations/
│   │   └── test_storage/
│   ├── integration/           # 統合テスト
│   │   ├── test_backlog_integration.py
│   │   ├── test_notion_integration.py
│   │   └── test_gcp_integration.py
│   └── fixtures/              # テストデータ
│       ├── sample_wbs.json
│       ├── sample_tasks.md
│       └── mock_responses/
├── config/                    # 設定ファイル
│   ├── settings.yaml          # 環境別設定
│   ├── categories.yaml        # カテゴリマスターデータ
│   └── issue_types.yaml       # 種別マスターデータ
├── scripts/                   # ユーティリティスクリプト
│   ├── deploy.sh              # Cloud Functionsデプロイスクリプト
│   ├── setup_mcp.py           # MCPサーバーセットアップ
│   └── test_local.py          # ローカルテスト実行
├── docs/                      # ドキュメント
│   ├── api.md                 # API仕様
│   ├── setup.md               # セットアップガイド
│   └── architecture.md        # アーキテクチャ設計
├── .spec-workflow/            # Spec Workflow管理
│   ├── templates/
│   ├── steering/
│   └── specs/
├── requirements.txt           # Python依存パッケージ
├── requirements-dev.txt       # 開発用依存パッケージ
├── pytest.ini                 # pytest設定
├── .env.example               # 環境変数サンプル
├── .gcloudignore              # Cloud Functionsデプロイ除外設定
└── README.md                  # プロジェクト概要
```

## Naming Conventions

### Files
- **モジュール**: `snake_case`（例: `wbs_service.py`, `task_merger.py`）
- **テストファイル**: `test_[module_name].py`（例: `test_wbs_service.py`）
- **設定ファイル**: `lowercase.yaml` または `lowercase.json`
- **スクリプト**: `snake_case.sh` または `snake_case.py`

### Code
- **クラス**: `PascalCase`（例: `WBSService`, `BacklogClient`, `TaskModel`）
- **関数/メソッド**: `snake_case`（例: `create_wbs()`, `merge_tasks()`, `detect_category()`）
- **定数**: `UPPER_SNAKE_CASE`（例: `MAX_RETRY_COUNT`, `DEFAULT_CATEGORY`）
- **変数**: `snake_case`（例: `task_list`, `file_url`, `metadata_dict`）
- **プライベートメソッド**: `_leading_underscore`（例: `_validate_input()`, `_parse_response()`）

### ディレクトリ
- すべて`lowercase`または`snake_case`（例: `services`, `integrations`, `test_fixtures`）

## Import Patterns

### Import Order
1. **標準ライブラリ**: Python標準ライブラリ
2. **サードパーティライブラリ**: pip でインストールしたパッケージ
3. **Google Cloudライブラリ**: google-cloud-* パッケージ
4. **ローカルモジュール**: 絶対インポート（`from src.services import ...`）
5. **相対インポート**: 同一パッケージ内（`from . import ...`, `from .. import ...`）

### Import 例
```python
# 1. 標準ライブラリ
import os
import json
from typing import List, Dict, Optional
from datetime import datetime

# 2. サードパーティライブラリ
import requests
from pydantic import BaseModel, Field

# 3. Google Cloudライブラリ
from google.cloud import storage, firestore, documentai
from google.cloud import logging as cloud_logging

# 4. ローカルモジュール（絶対インポート）
from src.models.task import Task, TaskCategory
from src.utils.logger import get_logger
from src.integrations.backlog.client import BacklogClient

# 5. 相対インポート（同一パッケージ内）
from .schemas import MCPRequest, MCPResponse
from ..utils.validators import validate_url
```

### Module Organization
- **絶対インポート優先**: `from src.services.wbs_service import WBSService`
- **相対インポートは同一パッケージ内のみ**: パッケージ内の結合度が高いモジュール間
- **循環インポート回避**: 必要に応じて型ヒント用の`TYPE_CHECKING`を使用

## Code Structure Patterns

### Module/Class Organization
各Pythonファイル内は以下の順序で構成：

1. **Docstring**: モジュールの説明（Google Style）
2. **Imports**: 上記のImport Order に従う
3. **Constants**: モジュールレベルの定数
4. **Type Definitions**: Pydanticモデル、TypedDict、Enum等
5. **Main Classes**: メインの実装クラス
6. **Helper Functions**: プライベートヘルパー関数（`_`始まり）
7. **Public API**: エクスポートする関数（`__all__`定義）

### ファイル例
```python
"""
WBS作成サービス

テンプレートと新規課題をマージしてBacklogに一括登録する機能を提供。
"""

# Imports...

# Constants
DEFAULT_CATEGORY = "要件定義"
MAX_BATCH_SIZE = 100

# Type Definitions
class TaskInput(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = DEFAULT_CATEGORY

# Main Classes
class WBSService:
    """WBS作成を管理するサービスクラス"""

    def __init__(self, backlog_client: BacklogClient):
        self.client = backlog_client
        self.logger = get_logger(__name__)

    def create_wbs(self, template_url: str, new_tasks: List[TaskInput]) -> Dict:
        """WBSを新規作成"""
        # Implementation...

# Helper Functions
def _merge_task_lists(template_tasks: List[Task], new_tasks: List[Task]) -> List[Task]:
    """内部ヘルパー: タスクリストをマージ"""
    # Implementation...

# Public API
__all__ = ["WBSService", "TaskInput"]
```

### Function/Method Organization
関数・メソッド内の構造：

1. **Docstring**: 関数の説明、引数、戻り値（Google Style）
2. **Input Validation**: 入力パラメータのバリデーション
3. **Core Logic**: メインの処理ロジック
4. **Error Handling**: try-except によるエラーハンドリング
5. **Logging**: 重要な処理ステップのログ記録
6. **Return**: 明示的な戻り値

## Code Organization Principles

1. **Single Responsibility**: 各モジュール・クラスは単一の責務を持つ
   - `wbs_service.py`: WBS作成に関するビジネスロジックのみ
   - `backlog/client.py`: Backlog APIとの通信のみ

2. **Modularity**: 再利用可能な小さなモジュールに分割
   - `processors/`: データ処理ロジックを独立モジュール化
   - `integrations/`: 外部サービス連携を独立モジュール化

3. **Testability**: テストしやすい構造
   - 依存性注入（DI）パターンの使用
   - モックしやすいインターフェース設計
   - `tests/`ディレクトリに対応するテスト構造

4. **Consistency**: プロジェクト全体で統一されたパターン
   - すべてのサービスクラスは`*Service`命名
   - すべてのクライアントクラスは`*Client`命名
   - すべてのモデルは`models/`に集約

## Module Boundaries

### Core vs Integrations
- **Core** (`services/`, `processors/`, `models/`): ビジネスロジックとデータ処理
- **Integrations** (`integrations/`): 外部サービス依存を隔離
- **依存方向**: Core → Integrations（逆方向の依存は禁止）

### Public API vs Internal
- **Public API**: `src/main.py` （Cloud Functionsエントリーポイント）
- **Internal Implementation**: 各種サービス、プロセッサー、クライアント
- **エクスポート**: `__all__`で公開APIを明示

### Stable vs Experimental
- **Stable**: `src/services/`, `src/integrations/`（本番コード）
- **Experimental**: `scripts/`（実験的スクリプト）
- **分離**: 実験的コードは本番コードに影響を与えない

### Dependencies Direction
```
main.py
  ↓
services/ ← mcp/
  ↓
processors/ ← integrations/
  ↓
storage/ ← models/ ← utils/
```

依存方向のルール：
- 上位層は下位層に依存可能
- 下位層は上位層に依存不可
- 同一層内の依存は最小限に

## Code Size Guidelines

- **ファイルサイズ**: 1ファイル500行以内を目安（最大1000行）
- **関数/メソッドサイズ**: 1関数50行以内を目安（最大100行）
- **クラス複雑性**: 1クラス10メソッド以内を目安
- **ネスト深度**: 最大4レベルまで（それ以上は関数分割）
- **引数の数**: 1関数5引数以内（それ以上はデータクラス使用）

### リファクタリング基準
- 500行超えたらファイル分割を検討
- 50行超えたら関数分割を検討
- ネスト3レベル超えたら早期リターンやヘルパー関数を検討

## MCP Server Structure

### MCPサーバーの責務分離
```
src/mcp/
├── server.py          # MCPサーバー本体（リクエスト受信、ルーティング）
├── handlers.py        # ハンドラー（サービス層への委譲）
└── schemas.py         # リクエスト/レスポンススキーマ
```

### 分離原則
- **MCPサーバー**: プロトコル処理とリクエスト/レスポンス変換のみ
- **サービス層**: ビジネスロジック実装
- **統合層**: 外部MCP（Backlog、Notion）との通信

### エントリーポイント
```python
# src/main.py
from src.mcp.server import create_mcp_server

def main(request):
    """Cloud Functions エントリーポイント"""
    server = create_mcp_server()
    return server.handle_request(request)
```

## Documentation Standards

### Docstring規約
- **スタイル**: Google Style Docstrings
- **必須対象**: すべての公開関数、クラス、メソッド
- **推奨対象**: 複雑なプライベート関数

### Docstring例
```python
def merge_tasks(template_tasks: List[Task], new_tasks: List[Task]) -> List[Task]:
    """テンプレートタスクと新規タスクをマージする。

    新規タスクのカテゴリを判定し、テンプレートタスクの適切な位置に
    挿入して統合されたタスクリストを生成する。

    Args:
        template_tasks: テンプレートから取得したタスクのリスト
        new_tasks: 新規に追加するタスクのリスト

    Returns:
        マージされたタスクのリスト（カテゴリ順にソート）

    Raises:
        ValueError: タスクが空リストの場合
        CategoryNotFoundError: カテゴリ判定に失敗した場合
    """
    # Implementation...
```

### コメント規約
- **複雑なロジック**: アルゴリズムの説明を記載
- **ビジネスルール**: なぜそのように実装したか理由を記載
- **TODO/FIXME**: 将来の改善点を明示

### READMEファイル
- **プロジェクトルート**: `README.md`（概要、セットアップ、使い方）
- **主要モジュール**: 各ディレクトリに`README.md`（責務と設計）

## Testing Structure

### テスト構成
- **Unit Tests** (`tests/unit/`): 各モジュールの単体テスト
- **Integration Tests** (`tests/integration/`): 外部サービス連携テスト
- **Fixtures** (`tests/fixtures/`): テストデータとモック

### テストファイル命名
- `tests/unit/test_[module_path]/test_[module_name].py`
- 例: `tests/unit/test_services/test_wbs_service.py`

### テストカバレッジ目標
- **全体**: 80%以上
- **ビジネスロジック**: 90%以上
- **統合層**: 70%以上（モックを活用）

## Environment Configuration

### 環境変数管理
- **開発環境**: `.env`ファイル（gitignore対象）
- **本番環境**: Google Secret Manager
- **設定例**: `.env.example`をリポジトリに含める

### 設定ファイル階層
1. デフォルト設定: `config/settings.yaml`
2. 環境変数オーバーライド: `.env`
3. Cloud Functions環境変数: デプロイ時設定

## Logging Strategy

### ログレベル
- **DEBUG**: 開発時の詳細情報
- **INFO**: 通常の処理フロー（タスク登録成功など）
- **WARNING**: 警告（リトライ発生など）
- **ERROR**: エラー（API呼び出し失敗など）
- **CRITICAL**: 致命的エラー（サービス停止レベル）

### ログ出力先
- **開発環境**: 標準出力
- **本番環境**: Google Cloud Logging

### ログ形式
- **構造化ログ**: JSON形式でメタデータ付与
- **トレース**: リクエストIDによる処理追跡
