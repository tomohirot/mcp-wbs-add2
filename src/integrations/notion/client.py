"""
Notion MCPクライアント

MCP プロトコル経由でNotion MCPサーバーと通信し、
Notion API操作を実行。
"""

import asyncio
from typing import Any, Dict, List, Optional

from ...utils.logger import Logger
from .models import (NotionBlock, NotionDatabase, NotionPage)


class NotionMCPClient:
    """Notion MCPクライアントクラス

    MCP プロトコルを使用してNotionサーバーと通信し、
    ページ・データベース取得などを実行。
    """

    def __init__(self, api_key: str, logger: Logger, timeout: int = 30):
        """NotionMCPClientを初期化

        Args:
            api_key: Notion APIキー（Integration Token）
            logger: ロガーインスタンス
            timeout: APIタイムアウト秒数（デフォルト: 30秒）
        """
        self.api_key = api_key
        self.logger = logger
        self.timeout = timeout
        self.api_base_url = "https://api.notion.com/v1"

        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 1.0  # 初期遅延秒数（指数バックオフで増加）

        self.logger.info("Initialized NotionMCPClient")

    async def _call_mcp(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """MCP経由でNotion APIを呼び出し（内部メソッド）

        Args:
            method: HTTPメソッド（GET, POST, PATCH, DELETE）
            endpoint: APIエンドポイント（例: /pages/:id）
            params: クエリパラメータ
            data: リクエストボディ

        Returns:
            APIレスポンスデータ

        Raises:
            Exception: API呼び出し失敗時
        """
        url = f"{self.api_base_url}{endpoint}"

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
                #     "notion_api",
                #     {
                #         "method": method,
                #         "url": url,
                #         "headers": {
                #             "Authorization": f"Bearer {self.api_key}",
                #             "Notion-Version": "2022-06-28"
                #         },
                #         "params": params,
                #         "json": data,
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
        """NotionからURLのデータを取得

        Args:
            url: Notion URL（ページまたはデータベース）

        Returns:
            取得したデータ（階層構造を含む）
            - type: "page" or "database"
            - data: NotionPageまたはNotionDatabaseオブジェクト
            - blocks: ページの場合、子ブロックリスト
            - rows: データベースの場合、行（ページ）リスト

        Raises:
            ValueError: 無効なURL
            Exception: データ取得失敗
        """
        self.logger.info(f"Fetching data from Notion URL: {url}")

        # URLからリソースIDを抽出
        resource_id = self._extract_id_from_url(url)
        if not resource_id:
            raise ValueError(f"Invalid Notion URL: {url}")

        # まずページとして取得を試みる
        try:
            result = await self._fetch_page_with_blocks(resource_id)
            self.logger.info(f"Successfully fetched page data from URL: {url}")
            return result

        except Exception as page_error:
            self.logger.debug(
                f"Failed to fetch as page, trying as database: {str(page_error)}"
            )

            # ページ取得失敗の場合、データベースとして取得を試みる
            try:
                result = await self._fetch_database_with_rows(resource_id)
                self.logger.info(f"Successfully fetched database data from URL: {url}")
                return result

            except Exception as db_error:
                self.logger.error(
                    f"Failed to fetch data from URL {url}: "
                    f"page error={str(page_error)}, db error={str(db_error)}"
                )
                raise ValueError(
                    f"Could not fetch data from URL as page or database: {url}"
                )

    async def _fetch_page_with_blocks(self, page_id: str) -> Dict[str, Any]:
        """ページとその子ブロックを取得（内部メソッド）

        Args:
            page_id: ページID

        Returns:
            ページデータと子ブロック
        """
        # ページ情報を取得
        page_response = await self._call_mcp("GET", f"/pages/{page_id}")

        # レスポンスをNotionPageモデルに変換
        try:
            page = NotionPage(**page_response) if page_response else None
        except (TypeError, ValueError) as e:
            self.logger.warning(f"Failed to convert page response to model: {str(e)}")
            page = page_response

        # 子ブロックを取得
        blocks_response = await self._call_mcp("GET", f"/blocks/{page_id}/children")

        # ブロックリストをNotionBlockモデルに変換
        blocks = []
        for block_data in blocks_response.get("results", []):
            try:
                blocks.append(NotionBlock(**block_data))
            except (TypeError, ValueError) as e:
                self.logger.warning(
                    f"Failed to convert block to model: {str(e)}, using raw data"
                )
                blocks.append(block_data)

        return {"type": "page", "data": page, "blocks": blocks}

    async def _fetch_database_with_rows(self, database_id: str) -> Dict[str, Any]:
        """データベースとその行を取得（内部メソッド）

        Args:
            database_id: データベースID

        Returns:
            データベースデータと行リスト
        """
        # データベース情報を取得
        database_response = await self._call_mcp("GET", f"/databases/{database_id}")

        # レスポンスをNotionDatabaseモデルに変換
        try:
            database = (
                NotionDatabase(**database_response) if database_response else None
            )
        except (TypeError, ValueError) as e:
            self.logger.warning(
                f"Failed to convert database response to model: {str(e)}"
            )
            database = database_response

        # データベースの行（ページ）を取得
        rows_response = await self._call_mcp(
            "POST",
            f"/databases/{database_id}/query",
            data={"page_size": 100},  # 最大100件取得
        )

        # 行リストをNotionPageモデルに変換
        rows = []
        for row_data in rows_response.get("results", []):
            try:
                rows.append(NotionPage(**row_data))
            except (TypeError, ValueError) as e:
                self.logger.warning(
                    f"Failed to convert row to model: {str(e)}, using raw data"
                )
                rows.append(row_data)

        return {"type": "database", "data": database, "rows": rows}

    async def get_page(self, page_id: str) -> NotionPage:
        """ページ情報を取得

        Args:
            page_id: ページID（UUID形式）

        Returns:
            Notionページ

        Raises:
            Exception: ページ取得失敗
        """
        self.logger.info(f"Getting Notion page: {page_id}")

        response = await self._call_mcp("GET", f"/pages/{page_id}")

        # レスポンスをNotionPageモデルに変換
        try:
            page = NotionPage(**response) if response else None
            if not page:
                # プレースホルダー（空レスポンスの場合）
                page = NotionPage(
                    id=page_id,
                    created_time="2023-01-01T00:00:00.000Z",
                    last_edited_time="2023-01-01T00:00:00.000Z",
                    properties={},
                    parent={},
                    url=f"https://notion.so/{page_id}",
                )
        except (TypeError, ValueError) as e:
            self.logger.warning(
                f"Failed to convert page response to model: {str(e)}, using placeholder"
            )
            page = NotionPage(
                id=page_id,
                created_time="2023-01-01T00:00:00.000Z",
                last_edited_time="2023-01-01T00:00:00.000Z",
                properties={},
                parent={},
                url=f"https://notion.so/{page_id}",
            )

        self.logger.info(f"Retrieved Notion page: {page_id}")
        return page

    async def get_blocks(self, block_id: str) -> List[NotionBlock]:
        """ブロックの子ブロックリストを取得

        Args:
            block_id: ブロックID（ページIDも可）

        Returns:
            子ブロックリスト

        Raises:
            Exception: ブロック取得失敗
        """
        self.logger.info(f"Getting blocks for: {block_id}")

        response = await self._call_mcp("GET", f"/blocks/{block_id}/children")

        # レスポンスをNotionBlockモデルに変換
        blocks = []
        for block_data in response.get("results", []):
            try:
                blocks.append(NotionBlock(**block_data))
            except (TypeError, ValueError) as e:
                self.logger.warning(
                    f"Failed to convert block to model: {str(e)}, skipping"
                )

        self.logger.info(f"Retrieved {len(blocks)} blocks for {block_id}")
        return blocks

    async def get_database(self, database_id: str) -> NotionDatabase:
        """データベース情報を取得

        Args:
            database_id: データベースID（UUID形式）

        Returns:
            Notionデータベース

        Raises:
            Exception: データベース取得失敗
        """
        self.logger.info(f"Getting Notion database: {database_id}")

        response = await self._call_mcp("GET", f"/databases/{database_id}")

        # レスポンスをNotionDatabaseモデルに変換
        try:
            database = NotionDatabase(**response) if response else None
            if not database:
                # プレースホルダー（空レスポンスの場合）
                database = NotionDatabase(
                    id=database_id,
                    created_time="2023-01-01T00:00:00.000Z",
                    last_edited_time="2023-01-01T00:00:00.000Z",
                    title=[],
                    properties={},
                    parent={},
                    url=f"https://notion.so/{database_id}",
                )
        except (TypeError, ValueError) as e:
            self.logger.warning(
                f"Failed to convert database response to model: {str(e)}, using placeholder"
            )
            database = NotionDatabase(
                id=database_id,
                created_time="2023-01-01T00:00:00.000Z",
                last_edited_time="2023-01-01T00:00:00.000Z",
                title=[],
                properties={},
                parent={},
                url=f"https://notion.so/{database_id}",
            )

        self.logger.info(f"Retrieved Notion database: {database_id}")
        return database

    async def query_database(
        self,
        database_id: str,
        filter_conditions: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100,
    ) -> List[NotionPage]:
        """データベースをクエリして行を取得

        Args:
            database_id: データベースID
            filter_conditions: フィルター条件
            sorts: ソート条件
            page_size: 取得件数（最大100）

        Returns:
            データベース行（Notionページ）リスト

        Raises:
            Exception: クエリ失敗
        """
        self.logger.info(
            f"Querying Notion database: {database_id} (page_size={page_size})"
        )

        query_data = {"page_size": min(page_size, 100)}

        if filter_conditions:
            query_data["filter"] = filter_conditions

        if sorts:
            query_data["sorts"] = sorts

        response = await self._call_mcp(
            "POST", f"/databases/{database_id}/query", data=query_data
        )

        # レスポンスをNotionPageモデルに変換
        pages = []
        for page_data in response.get("results", []):
            try:
                pages.append(NotionPage(**page_data))
            except (TypeError, ValueError) as e:
                self.logger.warning(
                    f"Failed to convert page to model: {str(e)}, skipping"
                )

        self.logger.info(f"Retrieved {len(pages)} rows from database {database_id}")
        return pages

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """NotionURLからリソースIDを抽出（内部メソッド）

        Args:
            url: Notion URL

        Returns:
            リソースID（UUID形式）、抽出失敗時はNone
        """
        # Notion URLの一般的なパターン:
        # https://www.notion.so/workspace/Page-Title-32文字のID
        # https://www.notion.so/32文字のID

        import re

        # 32文字の英数字（ハイフンなし）またはUUID形式を抽出
        pattern = r"([a-f0-9]{32})|([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
        match = re.search(pattern, url.lower())

        if match:
            # ハイフンなしの32文字IDをUUID形式に変換
            id_str = match.group(1) or match.group(2)
            if "-" not in id_str:
                # 32文字をUUID形式に変換: 8-4-4-4-12
                id_str = (
                    f"{id_str[0:8]}-{id_str[8:12]}-{id_str[12:16]}-"
                    f"{id_str[16:20]}-{id_str[20:32]}"
                )
            return id_str

        self.logger.warning(f"Could not extract ID from URL: {url}")
        return None
