"""
MCP サーバーセットアップ

MCP サーバーを初期化し、ハンドラーを登録。
"""

from typing import Any, Dict

from ..utils.config import get_config
from ..utils.logger import Logger
from .handlers import handle_create_wbs
from .schemas import CreateWBSRequest


async def create_mcp_server(logger: Logger) -> Dict[str, Any]:
    """MCP サーバーを作成してハンドラーを登録

    Args:
        logger: ロガーインスタンス

    Returns:
        MCP サーバー設定辞書
    """
    logger.info("Creating MCP server")

    config = get_config()

    # TODO: 実際のMCP SDK を使用してサーバーを作成
    # 現在はプレースホルダー実装
    #
    # 実装例:
    # from mcp import Server
    # server = Server(
    #     name="wbs-creation-server",
    #     version="1.0.0"
    # )
    #
    # # ハンドラーを登録
    # server.add_handler(
    #     "create_wbs",
    #     handle_create_wbs,
    #     request_schema=CreateWBSRequest
    # )
    #
    # return server

    # プレースホルダー: サーバー設定を辞書で返す
    server_config = {
        "name": "wbs-creation-server",
        "version": "1.0.0",
        "handlers": {
            "create_wbs": {
                "function": handle_create_wbs,
                "request_schema": CreateWBSRequest,
            }
        },
        "config": {
            "gcp_project_id": config.gcp_project_id,
            "environment": "production",
        },
    }

    logger.info("MCP server created successfully")
    return server_config


def get_server_metadata() -> Dict[str, Any]:
    """サーバーメタデータを取得

    Returns:
        サーバーメタデータ辞書
    """
    return {
        "name": "WBS Creation MCP Server",
        "version": "1.0.0",
        "description": "MCP server for automated WBS creation and Backlog registration",
        "capabilities": ["create_wbs"],
        "supported_services": ["Backlog", "Notion"],
    }
