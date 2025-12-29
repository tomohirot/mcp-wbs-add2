"""
MCP ハンドラー

WBS作成リクエストを処理するハンドラー関数。
"""

import uuid

from ..models.task import Task
from ..services.wbs_service import WBSService
from ..utils.logger import Logger
from .schemas import CreateWBSRequest, CreateWBSResponse, TaskSummary


async def handle_create_wbs(
    request: CreateWBSRequest, wbs_service: WBSService, logger: Logger
) -> CreateWBSResponse:
    """WBS作成リクエストをハンドリング

    MCPプロトコル経由で受信したリクエストを処理し、
    WBSServiceに委譲してWBS作成を実行。

    処理フロー:
    1. リクエストIDを生成
    2. リクエストをバリデーション（Pydanticによる自動検証）
    3. WBSServiceに処理を委譲
    4. 結果をCreateWBSResponseに変換
    5. レスポンスを返却

    Args:
        request: WBS作成リクエスト
        wbs_service: WBSサービスインスタンス
        logger: ロガーインスタンス

    Returns:
        WBS作成レスポンス

    Raises:
        なし（すべてのエラーをキャッチしてレスポンスに含める）
    """
    # リクエストIDを生成（ロギング用）
    request_id = str(uuid.uuid4())

    logger.info(
        f"[{request_id}] WBS creation request received: "
        f"template_url={request.template_url}, project_key={request.project_key}"
    )

    try:
        # === リクエストバリデーション ===
        # Pydanticにより自動的に検証済み
        logger.debug(f"[{request_id}] Request validation passed")

        # === WBSServiceに委譲 ===
        logger.info(f"[{request_id}] Delegating to WBSService")

        result = await wbs_service.create_wbs(
            template_url=request.template_url,
            new_tasks_text=request.new_tasks_text,
            project_key=request.project_key,
        )

        # === レスポンス作成 ===
        logger.info(
            f"[{request_id}] WBS creation completed: "
            f"success={result.success}, "
            f"registered={len(result.registered_tasks)}, "
            f"skipped={len(result.skipped_tasks)}"
        )

        response = CreateWBSResponse(
            success=result.success,
            registered_tasks=[
                _task_to_summary(task) for task in result.registered_tasks
            ],
            skipped_tasks=[_task_to_summary(task) for task in result.skipped_tasks],
            error_message=result.error_message,
            metadata_id=result.metadata_id,
            master_data_created=result.master_data_created,
            total_registered=len(result.registered_tasks),
            total_skipped=len(result.skipped_tasks),
        )

        logger.info(f"[{request_id}] Response created successfully")
        return response

    except Exception as e:
        # === エラー処理 ===
        logger.error(
            f"[{request_id}] Unexpected error in handler: {str(e)}", exc_info=True
        )

        # エラーレスポンスを返却
        return CreateWBSResponse(
            success=False,
            error_message=f"Internal error: {str(e)}",
            registered_tasks=[],
            skipped_tasks=[],
            total_registered=0,
            total_skipped=0,
        )


def _task_to_summary(task: Task) -> TaskSummary:
    """TaskモデルをTaskSummaryに変換

    Args:
        task: Taskモデル

    Returns:
        TaskSummaryモデル
    """
    # CategoryEnumをstr値に変換
    if task.category:
        # CategoryEnumの場合は.valueで日本語を取得
        # (CategoryEnumはstr, Enumを継承しているが、strだと"CategoryEnum.X"になる)
        category_str = (
            task.category.value
            if hasattr(task.category, "value")
            else str(task.category)
        )
    else:
        category_str = "未分類"

    return TaskSummary(
        title=task.title,
        description=task.description,
        category=category_str,
        priority=task.priority,
        assignee=task.assignee,
    )
