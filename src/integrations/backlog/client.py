"""
Backlog MCPクライアント

MCP プロトコル経由でBacklog MCPサーバーと通信し、
Backlog API操作を実行。
"""

import asyncio
from typing import Any, Dict, List, Optional

from ...models.task import Task
from ...utils.logger import Logger
from .models import (BacklogTask, Category, CustomField, CustomFieldInput,
                     IssueType)


class BacklogMCPClient:
    """Backlog MCPクライアントクラス

    MCP プロトコルを使用してBacklogサーバーと通信し、
    タスク登録、マスターデータ管理などを実行。
    """

    def __init__(self, api_key: str, space_url: str, logger: Logger, timeout: int = 30):
        """BacklogMCPClientを初期化

        Args:
            api_key: Backlog APIキー
            space_url: BacklogスペースURL（例: https://your-space.backlog.com）
            logger: ロガーインスタンス
            timeout: APIタイムアウト秒数（デフォルト: 30秒）
        """
        self.api_key = api_key
        self.space_url = space_url.rstrip("/")
        self.logger = logger
        self.timeout = timeout

        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 1.0  # 初期遅延秒数（指数バックオフで増加）

        self.logger.info(f"Initialized BacklogMCPClient for space: {self.space_url}")

    async def _call_mcp(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """MCP経由でBacklog APIを呼び出し（内部メソッド）

        Args:
            method: HTTPメソッド（GET, POST, PATCH, DELETE）
            endpoint: APIエンドポイント（例: /api/v2/issues）
            params: クエリパラメータ
            data: リクエストボディ

        Returns:
            APIレスポンスデータ

        Raises:
            Exception: API呼び出し失敗時
        """
        url = f"{self.space_url}{endpoint}"

        # APIキーをパラメータに追加
        if params is None:
            params = {}
        params["apiKey"] = self.api_key

        # リトライロジック付きでAPI呼び出し
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(
                    f"MCP call: {method} {url} (attempt {attempt + 1}/{self.max_retries})"
                )

                # TODO: 実際のMCP SDKクライアントを使用してAPI呼び出し
                # 現在はプレースホルダー実装
                # 実装例:
                # response = await mcp_client.call_tool(
                #     "backlog_api",
                #     {
                #         "method": method,
                #         "url": url,
                #         "params": params,
                #         "data": data,
                #         "timeout": self.timeout
                #     }
                # )

                # プレースホルダー: 実際のMCP呼び出しに置き換える必要がある
                await asyncio.sleep(0.1)  # API呼び出しをシミュレート

                self.logger.info(f"MCP call successful: {method} {endpoint}")
                return {}  # プレースホルダー

            except Exception as e:
                self.logger.warning(
                    f"MCP call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}"
                )

                if attempt == self.max_retries - 1:
                    # 最終リトライ失敗
                    self.logger.error(
                        f"MCP call failed after {self.max_retries} attempts: {method} {endpoint}"
                    )
                    raise

                # 指数バックオフで待機
                delay = self.retry_delay * (2**attempt)
                await asyncio.sleep(delay)

    async def fetch_data(self, url: str) -> Dict[str, Any]:
        """BacklogからURLのデータを取得

        Args:
            url: Backlog URL（課題、Wiki、ファイルなど）

        Returns:
            取得したデータ（階層構造を含む）

        Raises:
            ValueError: 無効なURL
            Exception: データ取得失敗
        """
        self.logger.info(f"Fetching data from Backlog URL: {url}")

        # URLからリソースタイプとIDを抽出
        # TODO: URL解析ロジックを実装

        # MCP経由でデータ取得
        result = await self._call_mcp("GET", "/api/v2/issues", params={"url": url})

        self.logger.info(f"Successfully fetched data from URL: {url}")
        return result

    async def get_tasks(self, project_key: str) -> List[BacklogTask]:
        """プロジェクトのタスク一覧を取得

        Args:
            project_key: プロジェクトキー（例: PROJ）

        Returns:
            タスクリスト

        Raises:
            Exception: タスク取得失敗
        """
        self.logger.info(f"Getting tasks for project: {project_key}")

        # プロジェクトの課題を取得
        response = await self._call_mcp(
            "GET",
            "/api/v2/issues",
            params={"projectId[]": project_key, "count": 100},  # 最大取得件数
        )

        # TODO: レスポンスをBacklogTaskモデルに変換
        tasks = []  # プレースホルダー

        self.logger.info(f"Retrieved {len(tasks)} tasks for project {project_key}")
        return tasks

    async def create_tasks(
        self, project_key: str, tasks: List[Task]
    ) -> List[BacklogTask]:
        """タスクを一括登録

        Args:
            project_key: プロジェクトキー
            tasks: 登録するタスクリスト

        Returns:
            登録されたBacklogタスクリスト

        Raises:
            Exception: タスク登録失敗
        """
        self.logger.info(f"Creating {len(tasks)} tasks in project: {project_key}")

        created_tasks = []

        for task in tasks:
            try:
                # タスクをBacklog形式に変換
                task_data = {
                    "projectId": project_key,
                    "summary": task.title,
                    "description": task.description or "",
                    "issueTypeId": 1,  # TODO: 適切な種別IDを設定
                    "priorityId": self._convert_priority(task.priority),
                }

                # カテゴリを設定
                if task.category:
                    # TODO: カテゴリ名からIDへの変換
                    pass

                # 担当者を設定
                if task.assignee:
                    task_data["assigneeId"] = task.assignee

                # MCP経由でタスク作成
                response = await self._call_mcp(
                    "POST", "/api/v2/issues", data=task_data
                )

                # TODO: レスポンスをBacklogTaskに変換
                # created_task = BacklogTask(**response)
                # created_tasks.append(created_task)

                self.logger.debug(f"Created task: {task.title}")

            except Exception as e:
                self.logger.error(f"Failed to create task '{task.title}': {str(e)}")
                raise

        self.logger.info(
            f"Successfully created {len(created_tasks)} tasks in {project_key}"
        )
        return created_tasks

    async def get_issue_types(self, project_key: str) -> List[IssueType]:
        """種別一覧を取得

        Args:
            project_key: プロジェクトキー

        Returns:
            種別リスト

        Raises:
            Exception: 種別取得失敗
        """
        self.logger.info(f"Getting issue types for project: {project_key}")

        response = await self._call_mcp(
            "GET", f"/api/v2/projects/{project_key}/issueTypes"
        )

        # TODO: レスポンスをIssueTypeモデルに変換
        issue_types = []  # プレースホルダー

        self.logger.info(f"Retrieved {len(issue_types)} issue types for {project_key}")
        return issue_types

    async def create_issue_type(self, project_key: str, name: str) -> IssueType:
        """種別を作成

        Args:
            project_key: プロジェクトキー
            name: 種別名（例: 課題、リスク）

        Returns:
            作成された種別

        Raises:
            Exception: 種別作成失敗
        """
        self.logger.info(f"Creating issue type '{name}' in project: {project_key}")

        response = await self._call_mcp(
            "POST",
            f"/api/v2/projects/{project_key}/issueTypes",
            data={"name": name, "color": "#990000"},  # デフォルト色
        )

        # TODO: レスポンスをIssueTypeモデルに変換
        issue_type = IssueType(
            id=1, project_id=1, name=name, color="#990000", display_order=1
        )  # プレースホルダー

        self.logger.info(f"Created issue type: {name}")
        return issue_type

    async def get_categories(self, project_key: str) -> List[Category]:
        """カテゴリ一覧を取得

        Args:
            project_key: プロジェクトキー

        Returns:
            カテゴリリスト

        Raises:
            Exception: カテゴリ取得失敗
        """
        self.logger.info(f"Getting categories for project: {project_key}")

        response = await self._call_mcp(
            "GET", f"/api/v2/projects/{project_key}/categories"
        )

        # TODO: レスポンスをCategoryモデルに変換
        categories = []  # プレースホルダー

        self.logger.info(f"Retrieved {len(categories)} categories for {project_key}")
        return categories

    async def create_category(self, project_key: str, name: str) -> Category:
        """カテゴリを作成

        Args:
            project_key: プロジェクトキー
            name: カテゴリ名（例: 事前準備、要件定義）

        Returns:
            作成されたカテゴリ

        Raises:
            Exception: カテゴリ作成失敗
        """
        self.logger.info(f"Creating category '{name}' in project: {project_key}")

        response = await self._call_mcp(
            "POST", f"/api/v2/projects/{project_key}/categories", data={"name": name}
        )

        # TODO: レスポンスをCategoryモデルに変換
        category = Category(id=1, name=name, display_order=1)  # プレースホルダー

        self.logger.info(f"Created category: {name}")
        return category

    async def get_custom_fields(self, project_key: str) -> List[CustomField]:
        """カスタム属性一覧を取得

        Args:
            project_key: プロジェクトキー

        Returns:
            カスタム属性リスト

        Raises:
            Exception: カスタム属性取得失敗
        """
        self.logger.info(f"Getting custom fields for project: {project_key}")

        response = await self._call_mcp(
            "GET", f"/api/v2/projects/{project_key}/customFields"
        )

        # TODO: レスポンスをCustomFieldモデルに変換
        custom_fields = []  # プレースホルダー

        self.logger.info(
            f"Retrieved {len(custom_fields)} custom fields for {project_key}"
        )
        return custom_fields

    async def create_custom_field(
        self, project_key: str, field: CustomFieldInput
    ) -> CustomField:
        """カスタム属性を作成

        Args:
            project_key: プロジェクトキー
            field: カスタム属性定義

        Returns:
            作成されたカスタム属性

        Raises:
            Exception: カスタム属性作成失敗
        """
        self.logger.info(
            f"Creating custom field '{field.name}' in project: {project_key}"
        )

        field_data = {
            "name": field.name,
            "typeId": field.type_id,
            "required": field.required,
        }

        if field.description:
            field_data["description"] = field.description

        if field.applicable_issue_types:
            field_data["applicableIssueTypes"] = field.applicable_issue_types

        response = await self._call_mcp(
            "POST", f"/api/v2/projects/{project_key}/customFields", data=field_data
        )

        # TODO: レスポンスをCustomFieldモデルに変換
        custom_field = CustomField(
            id=1, name=field.name, type_id=field.type_id, required=field.required
        )  # プレースホルダー

        self.logger.info(f"Created custom field: {field.name}")
        return custom_field

    def _convert_priority(self, priority: Optional[str]) -> int:
        """優先度文字列をBacklog優先度IDに変換

        Args:
            priority: 優先度文字列（高、中、低）

        Returns:
            Backlog優先度ID（2: 高、3: 中、4: 低）
        """
        if not priority:
            return 3  # デフォルト: 中

        priority_map = {"高": 2, "中": 3, "低": 4}

        return priority_map.get(priority, 3)
