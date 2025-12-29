"""
MCPクライアントファクトリ

サービスタイプに応じたMCPクライアントを生成。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ..models.enums import ServiceType
from ..utils.config import get_config
from ..utils.logger import Logger

if TYPE_CHECKING:
    from .backlog.client import BacklogMCPClient
    from .notion.client import NotionMCPClient


class MCPFactory:
    """MCPクライアントファクトリクラス

    サービスタイプ（Backlog/Notion）に応じて適切なMCPクライアントを生成。
    """

    def __init__(self, logger: Logger):
        """MCPFactoryを初期化

        Args:
            logger: ロガーインスタンス
        """
        self.logger = logger
        self.config = get_config()

    def create_client(
        self, service_type: ServiceType
    ) -> Union[BacklogMCPClient, NotionMCPClient]:
        """サービスタイプに応じたMCPクライアントを生成

        Args:
            service_type: サービスタイプ

        Returns:
            MCPクライアント（BacklogMCPClientまたはNotionMCPClient）

        Raises:
            ValueError: サポートされていないサービスタイプの場合
        """
        # 循環インポートを避けるため、メソッド内でインポート
        from .backlog.client import BacklogMCPClient
        from .notion.client import NotionMCPClient

        if service_type == ServiceType.BACKLOG:
            self.logger.info("Creating Backlog MCP client")
            return BacklogMCPClient(
                api_key=self.config.backlog_api_key,
                space_url=self.config.backlog_space_url,
                logger=self.logger,
            )

        elif service_type == ServiceType.NOTION:
            self.logger.info("Creating Notion MCP client")
            return NotionMCPClient(
                api_key=self.config.notion_api_key, logger=self.logger
            )

        else:
            raise ValueError(f"サポートされていないサービスタイプです: {service_type}")
