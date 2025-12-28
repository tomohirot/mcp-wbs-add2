"""
Cloud Functions エントリーポイント

Google Cloud Functions用のメインエントリーポイント。
HTTP リクエストを受信し、MCP ハンドラーに委譲。
"""

import json
import traceback
from typing import Tuple

from flask import Request, Response

from .mcp.schemas import CreateWBSRequest, CreateWBSResponse
from .mcp.server import get_server_metadata
from .utils.config import get_config
from .utils.logger import Logger

# 依存性注入用のサービスインスタンス（グローバル変数）
# Cloud Functionsでは起動時に初期化されキャッシュされる
_logger = None
_services = None


def _initialize_services() -> dict:
    """サービスを初期化（初回呼び出し時のみ）

    Returns:
        初期化されたサービス辞書
    """
    global _logger, _services

    if _services is not None:
        return _services

    # ロガー初期化
    _logger = Logger(request_id="startup")
    _logger.info("Initializing services for Cloud Functions")

    config = get_config()

    # TODO: 実際のサービスインスタンスを初期化
    # 各サービスを依存性注入パターンで構築
    #
    # 実装例:
    # from .processors.url_parser import URLParser
    # from .processors.document_processor import DocumentProcessor
    # from .processors.converter import Converter
    # from .services.category_detector import CategoryDetector
    # from .services.task_merger import TaskMerger
    # from .services.master_service import MasterService
    # from .services.wbs_service import WBSService
    # from .integrations.mcp_factory import MCPFactory
    # from .integrations.backlog.client import BacklogMCPClient
    # from .storage import StorageManager
    #
    # # 依存性を順に構築
    # url_parser = URLParser()
    # category_detector = CategoryDetector()
    # converter = Converter()
    # # ... 他のサービスも構築
    #
    # wbs_service = WBSService(
    #     master_service=master_service,
    #     url_parser=url_parser,
    #     ...
    # )

    # プレースホルダー実装
    _services = {
        "logger": _logger,
        "config": config,
        "wbs_service": None,  # 実際のWBSServiceインスタンスに置き換え
    }

    _logger.info("Services initialized successfully")
    return _services


def wbs_create(request: Request) -> Tuple[Response, int]:
    """Cloud Functions エントリーポイント: WBS作成

    HTTP POSTリクエストを受信し、WBS作成処理を実行。

    リクエスト形式:
        POST /wbs-create
        Content-Type: application/json
        Body: {
            "template_url": "https://...",
            "new_tasks_text": "...",
            "project_key": "PROJ"
        }

    レスポンス形式:
        Content-Type: application/json
        Body: CreateWBSResponse schema

    Args:
        request: Flask Request オブジェクト

    Returns:
        (Response, status_code) タプル
    """
    # サービス初期化
    services = _initialize_services()
    logger = services["logger"]

    try:
        logger.info(f"Received request: {request.method} {request.path}")

        # CORSヘッダー設定
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # 本番環境では適切なオリジンに制限
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        # OPTIONSリクエスト（プリフライト）処理
        if request.method == "OPTIONS":
            return Response("", status=204, headers=headers)

        # POSTメソッドのみ受け付ける
        if request.method != "POST":
            error_response = {
                "success": False,
                "error_message": f"Method {request.method} not allowed. Use POST.",
            }
            return Response(json.dumps(error_response), status=405, headers=headers)

        # リクエストボディを解析
        request_data = request.get_json(silent=True)
        if not request_data:
            error_response = {
                "success": False,
                "error_message": "Invalid JSON in request body",
            }
            return Response(json.dumps(error_response), status=400, headers=headers)

        logger.info(f"Request data: {request_data}")

        # Pydanticスキーマでバリデーション
        try:
            CreateWBSRequest(**request_data)
        except Exception as e:
            logger.warning(f"Request validation failed: {str(e)}")
            error_response = {
                "success": False,
                "error_message": f"Request validation error: {str(e)}",
            }
            return Response(json.dumps(error_response), status=400, headers=headers)

        # TODO: ハンドラーを呼び出し
        # 実装例:
        # import asyncio
        # wbs_service = services["wbs_service"]
        # response = asyncio.run(
        #     handle_create_wbs(wbs_request, wbs_service, logger)
        # )

        # プレースホルダーレスポンス
        response = CreateWBSResponse(
            success=True,
            registered_tasks=[],
            skipped_tasks=[],
            metadata_id="placeholder",
            master_data_created=0,
            total_registered=0,
            total_skipped=0,
        )

        logger.info("WBS creation completed successfully")

        return Response(response.model_dump_json(), status=200, headers=headers)

    except Exception as e:
        logger.error(f"Unexpected error in Cloud Functions: {str(e)}")
        logger.error(traceback.format_exc())

        error_response = {
            "success": False,
            "error_message": f"Internal server error: {str(e)}",
        }

        return Response(
            json.dumps(error_response),
            status=500,
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        )


def health_check(request: Request) -> Tuple[Response, int]:
    """ヘルスチェックエンドポイント

    サーバーの稼働状態を確認。

    Args:
        request: Flask Request オブジェクト

    Returns:
        (Response, status_code) タプル
    """
    metadata = get_server_metadata()

    health_response = {"status": "healthy", "server": metadata}

    return Response(
        json.dumps(health_response),
        status=200,
        headers={"Content-Type": "application/json"},
    )
