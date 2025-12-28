"""
マスターデータサービス

Backlogプロジェクトのマスターデータ（種別、カテゴリ、カスタム属性）を
自動設定する機能を提供。
"""

from typing import List, Set

from ..integrations.backlog.client import BacklogMCPClient
from ..integrations.backlog.models import CustomFieldInput
from ..models.enums import CategoryEnum, IssueTypeEnum
from ..utils.logger import Logger

# 必要な種別（課題、リスク）
REQUIRED_ISSUE_TYPES = [
    IssueTypeEnum.TASK.value,  # "課題"
    IssueTypeEnum.RISK.value,  # "リスク"
]

# 必要なカテゴリ（7つすべて）
REQUIRED_CATEGORIES = [
    CategoryEnum.PREPARATION.value,  # "事前準備"
    CategoryEnum.REQUIREMENTS.value,  # "要件定義"
    CategoryEnum.BASIC_DESIGN.value,  # "基本設計"
    CategoryEnum.IMPLEMENTATION.value,  # "実装"
    CategoryEnum.TESTING.value,  # "テスト"
    CategoryEnum.RELEASE.value,  # "リリース"
    CategoryEnum.DELIVERY.value,  # "納品"
]

# 必要なカスタム属性
REQUIRED_CUSTOM_FIELDS = [
    {
        "name": "インプット",
        "type_id": 1,  # 文字列タイプ
        "description": "タスクのインプット（前提条件、入力データなど）",
    },
    {
        "name": "ゴール/アウトプット",
        "type_id": 2,  # テキストタイプ
        "description": "タスクのゴールとアウトプット（成果物、完了条件など）",
    },
]


class MasterDataResult:
    """マスターデータセットアップ結果"""

    def __init__(self):
        """結果を初期化"""
        self.created_issue_types: List[str] = []
        self.created_categories: List[str] = []
        self.created_custom_fields: List[str] = []
        self.errors: List[str] = []

    @property
    def success(self) -> bool:
        """セットアップが成功したか

        Returns:
            エラーがない場合True
        """
        return len(self.errors) == 0

    @property
    def total_created(self) -> int:
        """作成した項目の総数

        Returns:
            作成した種別、カテゴリ、カスタム属性の合計数
        """
        return (
            len(self.created_issue_types)
            + len(self.created_categories)
            + len(self.created_custom_fields)
        )


class MasterService:
    """マスターデータサービスクラス

    Backlogプロジェクトに必要なマスターデータを確認し、
    不足している項目を自動作成。
    """

    def __init__(self, backlog_client: BacklogMCPClient, logger: Logger):
        """MasterServiceを初期化

        Args:
            backlog_client: Backlog MCPクライアント
            logger: ロガーインスタンス
        """
        self.backlog_client = backlog_client
        self.logger = logger

    async def setup_master_data(self, project_key: str) -> MasterDataResult:
        """マスターデータをセットアップ

        処理フロー:
        1. 種別（課題、リスク）を確認・追加
        2. カテゴリ（7つすべて）を確認・追加
        3. カスタム属性（インプット、ゴール/アウトプット）を確認・追加

        Args:
            project_key: プロジェクトキー

        Returns:
            セットアップ結果
        """
        self.logger.info(f"Setting up master data for project: {project_key}")

        result = MasterDataResult()

        # 種別をセットアップ
        try:
            created_types = await self._ensure_issue_types(project_key)
            result.created_issue_types = created_types
            self.logger.info(
                f"Issue types setup complete: {len(created_types)} created"
            )
        except Exception as e:
            error_msg = f"Failed to setup issue types: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)

        # カテゴリをセットアップ
        try:
            created_cats = await self._ensure_categories(project_key)
            result.created_categories = created_cats
            self.logger.info(f"Categories setup complete: {len(created_cats)} created")
        except Exception as e:
            error_msg = f"Failed to setup categories: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)

        # カスタム属性をセットアップ
        try:
            created_fields = await self._ensure_custom_fields(project_key)
            result.created_custom_fields = created_fields
            self.logger.info(
                f"Custom fields setup complete: {len(created_fields)} created"
            )
        except Exception as e:
            error_msg = f"Failed to setup custom fields: {str(e)}"
            self.logger.error(error_msg)
            result.errors.append(error_msg)

        # 結果サマリーをログ出力
        if result.success:
            self.logger.info(
                f"Master data setup successful: {result.total_created} items created"
            )
        else:
            self.logger.warning(
                f"Master data setup completed with errors: {len(result.errors)} errors"
            )

        return result

    async def _ensure_issue_types(self, project_key: str) -> List[str]:
        """種別（課題、リスク）を確認・追加

        Args:
            project_key: プロジェクトキー

        Returns:
            作成した種別名のリスト

        Raises:
            Exception: 種別の取得または作成に失敗
        """
        self.logger.debug(f"Ensuring issue types for project: {project_key}")

        # 既存の種別を取得
        existing_types = await self.backlog_client.get_issue_types(project_key)
        existing_type_names: Set[str] = {t.name for t in existing_types}

        self.logger.debug(
            f"Found {len(existing_types)} existing issue types: {existing_type_names}"
        )

        # 不足している種別を作成
        created_types = []

        for required_type in REQUIRED_ISSUE_TYPES:
            if required_type not in existing_type_names:
                self.logger.info(f"Creating missing issue type: {required_type}")
                try:
                    await self.backlog_client.create_issue_type(
                        project_key, required_type
                    )
                    created_types.append(required_type)
                    self.logger.info(f"Created issue type: {required_type}")
                except Exception as e:
                    self.logger.error(
                        f"Failed to create issue type '{required_type}': {str(e)}"
                    )
                    raise
            else:
                self.logger.debug(f"Issue type already exists: {required_type}")

        return created_types

    async def _ensure_categories(self, project_key: str) -> List[str]:
        """カテゴリ（全7種）を確認・追加

        Args:
            project_key: プロジェクトキー

        Returns:
            作成したカテゴリ名のリスト

        Raises:
            Exception: カテゴリの取得または作成に失敗
        """
        self.logger.debug(f"Ensuring categories for project: {project_key}")

        # 既存のカテゴリを取得
        existing_categories = await self.backlog_client.get_categories(project_key)
        existing_category_names: Set[str] = {c.name for c in existing_categories}

        self.logger.debug(
            f"Found {len(existing_categories)} existing categories: {existing_category_names}"
        )

        # 不足しているカテゴリを作成
        created_categories = []

        for required_category in REQUIRED_CATEGORIES:
            if required_category not in existing_category_names:
                self.logger.info(f"Creating missing category: {required_category}")
                try:
                    await self.backlog_client.create_category(
                        project_key, required_category
                    )
                    created_categories.append(required_category)
                    self.logger.info(f"Created category: {required_category}")
                except Exception as e:
                    self.logger.error(
                        f"Failed to create category '{required_category}': {str(e)}"
                    )
                    raise
            else:
                self.logger.debug(f"Category already exists: {required_category}")

        return created_categories

    async def _ensure_custom_fields(self, project_key: str) -> List[str]:
        """カスタム属性（インプット、ゴール/アウトプット）を確認・追加

        Args:
            project_key: プロジェクトキー

        Returns:
            作成したカスタム属性名のリスト

        Raises:
            Exception: カスタム属性の取得または作成に失敗
        """
        self.logger.debug(f"Ensuring custom fields for project: {project_key}")

        # 既存のカスタム属性を取得
        existing_fields = await self.backlog_client.get_custom_fields(project_key)
        existing_field_names: Set[str] = {f.name for f in existing_fields}

        self.logger.debug(
            f"Found {len(existing_fields)} existing custom fields: {existing_field_names}"
        )

        # 不足しているカスタム属性を作成
        created_fields = []

        for required_field in REQUIRED_CUSTOM_FIELDS:
            field_name = required_field["name"]

            if field_name not in existing_field_names:
                self.logger.info(f"Creating missing custom field: {field_name}")
                try:
                    field_input = CustomFieldInput(
                        name=field_name,
                        type_id=required_field["type_id"],
                        description=required_field.get("description"),
                        required=False,
                    )

                    await self.backlog_client.create_custom_field(
                        project_key, field_input
                    )
                    created_fields.append(field_name)
                    self.logger.info(f"Created custom field: {field_name}")
                except Exception as e:
                    self.logger.error(
                        f"Failed to create custom field '{field_name}': {str(e)}"
                    )
                    raise
            else:
                self.logger.debug(f"Custom field already exists: {field_name}")

        return created_fields
