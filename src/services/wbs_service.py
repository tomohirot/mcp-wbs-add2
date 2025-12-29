"""
WBSサービス

WBS作成プロセス全体をオーケストレーションし、
テンプレート取得から Backlog 登録までの完全なワークフローを実行。
"""

from typing import Any, Dict, List, Optional

from ..integrations.backlog.client import BacklogMCPClient
from ..integrations.mcp_factory import MCPFactory
from ..models.enums import ServiceType
from ..models.task import Task
from ..processors.converter import Converter
from ..processors.document_processor import DocumentProcessor
from ..processors.url_parser import URLParser
from ..storage import StorageManager
from ..utils.logger import Logger
from .master_service import MasterService
from .task_merger import TaskMerger


class WBSResult:
    """WBS作成結果"""

    def __init__(self):
        """結果を初期化"""
        self.success: bool = False
        self.registered_tasks: List[Task] = []
        self.skipped_tasks: List[Task] = []
        self.metadata_id: Optional[str] = None
        self.error_message: Optional[str] = None
        self.master_data_created: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            結果の辞書表現
        """
        return {
            "success": self.success,
            "registered_tasks": [t.model_dump() for t in self.registered_tasks],
            "skipped_tasks": [t.model_dump() for t in self.skipped_tasks],
            "metadata_id": self.metadata_id,
            "error_message": self.error_message,
            "master_data_created": self.master_data_created,
            "total_registered": len(self.registered_tasks),
            "total_skipped": len(self.skipped_tasks),
        }


class WBSService:
    """WBSサービスクラス

    WBS作成プロセス全体をオーケストレーション。
    依存性注入パターンを使用して各コンポーネントを統合。
    """

    def __init__(
        self,
        master_service: MasterService,
        url_parser: URLParser,
        mcp_factory: MCPFactory,
        document_processor: DocumentProcessor,
        converter: Converter,
        task_merger: TaskMerger,
        backlog_client: BacklogMCPClient,
        storage_manager: StorageManager,
        logger: Logger,
    ):
        """WBSServiceを初期化

        Args:
            master_service: マスターデータサービス
            url_parser: URL解析サービス
            mcp_factory: MCPクライアントファクトリ
            document_processor: ドキュメント処理サービス
            converter: データ変換サービス
            task_merger: タスクマージサービス
            backlog_client: Backlog MCPクライアント
            storage_manager: ストレージマネージャー
            logger: ロガー
        """
        self.master_service = master_service
        self.url_parser = url_parser
        self.mcp_factory = mcp_factory
        self.document_processor = document_processor
        self.converter = converter
        self.task_merger = task_merger
        self.backlog_client = backlog_client
        self.storage_manager = storage_manager
        self.logger = logger

    async def create_wbs(
        self, template_url: str, new_tasks_text: Optional[str], project_key: str
    ) -> WBSResult:
        """WBSを作成してBacklogに登録

        完全なワークフロー:
        1. マスターデータセットアップ
        2. URL解析（サービスタイプ判定）
        3. MCPクライアント作成
        4. テンプレート取得
        5. Document AI処理（必要な場合）
        6. データ変換
        7. ストレージ保存
        8. 新規タスク解析
        9. タスクマージ
        10. 重複チェック
        11. Backlog登録
        12. 結果コンパイル

        Args:
            template_url: テンプレートURL（Backlog or Notion）
            new_tasks_text: 新規タスクテキスト（オプション）
            project_key: Backlogプロジェクトキー

        Returns:
            WBS作成結果
        """
        result = WBSResult()

        try:
            self.logger.info(
                f"Starting WBS creation for project: {project_key}, "
                f"template: {template_url}"
            )

            # === Step 1: マスターデータセットアップ ===
            self.logger.info("Step 1: Setting up master data")
            master_result = await self.master_service.setup_master_data(project_key)

            if master_result.success:
                result.master_data_created = master_result.total_created
                self.logger.info(
                    f"Master data setup complete: {result.master_data_created} items created"
                )
            else:
                self.logger.warning(
                    f"Master data setup had errors (continuing anyway): "
                    f"{len(master_result.errors)} errors"
                )

            # === Step 2: URL解析 ===
            self.logger.info("Step 2: Parsing template URL")
            service_type = self.url_parser.parse_service_type(template_url)
            self.logger.info(f"Detected service type: {service_type}")

            # === Step 3: MCPクライアント作成 ===
            self.logger.info("Step 3: Creating MCP client")
            mcp_client = self.mcp_factory.create_client(service_type)
            self.logger.info(f"Created {service_type} MCP client")

            # === Step 4: テンプレート取得 ===
            self.logger.info("Step 4: Fetching template data")
            template_data = await mcp_client.fetch_data(template_url)
            self.logger.info("Template data fetched successfully")

            # === Step 5-6: Document AI処理 & データ変換 ===
            self.logger.info("Step 5-6: Processing and converting template data")
            template_tasks = await self._process_template_data(
                template_data, service_type
            )
            self.logger.info(f"Parsed {len(template_tasks)} tasks from template")

            # === Step 7: ストレージ保存 ===
            self.logger.info("Step 7: Saving template data to storage")
            metadata = await self.storage_manager.save_data(
                parent_url=template_url,
                file_url=template_url,
                file_name=f"{project_key}_template",
                data=template_data,
                format="json",
            )
            result.metadata_id = metadata.id
            self.logger.info(
                f"Saved to storage: version {metadata.version}, "
                f"metadata_id: {metadata.id}"
            )

            # === Step 8: 新規タスク解析 ===
            new_tasks: List[Task] = []
            if new_tasks_text:
                self.logger.info("Step 8: Parsing new tasks from text")
                new_tasks = self.converter.parse_tasks_from_text(new_tasks_text)
                self.logger.info(f"Parsed {len(new_tasks)} new tasks")
            else:
                self.logger.info("Step 8: No new tasks provided, skipping")

            # === Step 9: タスクマージ ===
            self.logger.info("Step 9: Merging template and new tasks")
            merged_tasks = self.task_merger.merge_tasks(template_tasks, new_tasks)
            self.logger.info(
                f"Merged tasks: {len(merged_tasks)} total "
                f"({len(template_tasks)} template + {len(new_tasks)} new)"
            )

            # === Step 10: 重複チェック ===
            self.logger.info("Step 10: Checking for duplicate tasks")
            (tasks_to_register, duplicates) = await self._check_duplicates(
                project_key, merged_tasks
            )
            result.skipped_tasks = duplicates
            self.logger.info(
                f"Duplicate check complete: {len(tasks_to_register)} to register, "
                f"{len(duplicates)} duplicates skipped"
            )

            # === Step 11: Backlog登録 ===
            if tasks_to_register:
                self.logger.info(
                    f"Step 11: Registering {len(tasks_to_register)} tasks to Backlog"
                )
                registered = await self.backlog_client.create_tasks(
                    project_key, tasks_to_register
                )
                result.registered_tasks = tasks_to_register
                self.logger.info(
                    f"Successfully registered {len(registered)} tasks to Backlog"
                )
            else:
                self.logger.info("Step 11: No tasks to register, skipping")

            # === Step 12: 結果コンパイル ===
            self.logger.info("Step 12: Compiling results")
            result.success = True
            self.logger.info(
                f"WBS creation complete: {len(result.registered_tasks)} registered, "
                f"{len(result.skipped_tasks)} skipped"
            )

        except Exception as e:
            self.logger.error(f"WBS creation failed: {str(e)}", exc_info=True)
            result.success = False
            result.error_message = str(e)

        return result

    async def _process_template_data(
        self, template_data: Dict[str, Any], service_type: ServiceType
    ) -> List[Task]:
        """テンプレートデータを処理してタスクリストを取得

        Args:
            template_data: MCP経由で取得したテンプレートデータ
            service_type: サービスタイプ（Backlog/Notion）

        Returns:
            タスクリスト

        Raises:
            Exception: データ処理失敗
        """
        # サービスタイプに応じてデータを解析
        if service_type == ServiceType.BACKLOG:
            # Backlogの場合、階層データをタスクリストに変換
            return self._parse_backlog_data(template_data)

        elif service_type == ServiceType.NOTION:
            # Notionの場合、ページ/データベースをタスクリストに変換
            return self._parse_notion_data(template_data)

        else:
            raise ValueError(f"Unsupported service type: {service_type}")

    def _parse_backlog_data(self, data: Dict[str, Any]) -> List[Task]:
        """Backlogデータをタスクリストに変換

        Args:
            data: Backlogデータ

        Returns:
            タスクリスト
        """
        # TODO: 実際のBacklogデータ構造に応じて実装
        # プレースホルダー実装
        self.logger.debug("Parsing Backlog data to tasks")
        return []

    def _parse_notion_data(self, data: Dict[str, Any]) -> List[Task]:
        """Notionデータをタスクリストに変換

        Args:
            data: Notionデータ

        Returns:
            タスクリスト
        """
        # TODO: 実際のNotionデータ構造に応じて実装
        # プレースホルダー実装
        self.logger.debug("Parsing Notion data to tasks")

        # Notionブロックからタスクを抽出する例
        if data.get("type") == "page" and "blocks" in data:
            blocks = data.get("blocks", [])
            # ブロックをテキストに変換
            text_content = self._extract_text_from_blocks(blocks)
            # テキストからタスクをパース
            return self.converter.parse_tasks_from_text(text_content)

        elif data.get("type") == "database" and "rows" in data:
            rows = data.get("rows", [])
            # データベース行からタスクを抽出
            tasks = []
            for row in rows:
                # TODO: 行のプロパティからTaskオブジェクトを構築
                pass
            return tasks

        return []

    def _extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Notionブロックリストからテキストを抽出

        Args:
            blocks: Notionブロックリスト

        Returns:
            結合されたテキスト
        """
        # TODO: 実際のNotionブロック構造に応じて実装
        # プレースホルダー実装
        return ""

    async def _check_duplicates(
        self, project_key: str, tasks: List[Task]
    ) -> tuple[List[Task], List[Task]]:
        """既存タスクとの重複をチェック

        Args:
            project_key: プロジェクトキー
            tasks: チェックするタスクリスト

        Returns:
            (登録するタスク, 重複タスク) のタプル
        """
        self.logger.debug(f"Checking duplicates for {len(tasks)} tasks")

        try:
            # 既存タスクを取得
            existing_tasks = await self.backlog_client.get_tasks(project_key)
            existing_titles = {t.summary.lower() for t in existing_tasks}

            # 重複をフィルタリング
            to_register = []
            duplicates = []

            for task in tasks:
                if task.title.lower() in existing_titles:
                    duplicates.append(task)
                    self.logger.debug(f"Duplicate found: {task.title}")
                else:
                    to_register.append(task)

            return (to_register, duplicates)

        except Exception as e:
            self.logger.warning(
                f"Failed to check duplicates (continuing with all tasks): {str(e)}"
            )
            # エラー時は全タスクを登録対象とする
            return (tasks, [])
