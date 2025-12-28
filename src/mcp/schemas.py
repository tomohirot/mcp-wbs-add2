"""
MCP スキーマ定義

WBS作成APIのリクエスト/レスポンススキーマをPydanticで定義。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class CreateWBSRequest(BaseModel):
    """WBS作成リクエストスキーマ

    MCPプロトコル経由で受信するリクエストデータ。
    """

    template_url: str = Field(
        ...,
        description="テンプレートURL（Backlog or Notion）",
        min_length=1,
        examples=["https://your-space.backlog.com/view/PROJ-123"],
    )

    new_tasks_text: Optional[str] = Field(
        None,
        description="新規タスクテキスト（オプション、Markdown形式）",
        examples=[
            "- タスク1 | priority: 高 | category: 実装\n" "- タスク2 | priority: 中"
        ],
    )

    project_key: str = Field(
        ...,
        description="Backlogプロジェクトキー",
        min_length=1,
        max_length=50,
        examples=["PROJ", "WBS"],
    )

    class Config:
        """Pydantic設定"""

        json_schema_extra = {
            "example": {
                "template_url": "https://your-space.backlog.com/view/PROJ-123",
                "new_tasks_text": "- 追加タスク1 | priority: 高\n- 追加タスク2",
                "project_key": "PROJ",
            }
        }


class TaskSummary(BaseModel):
    """タスクサマリースキーマ

    レスポンスに含まれるタスク情報の簡略版。
    """

    title: str = Field(..., description="タスクタイトル")
    description: Optional[str] = Field(None, description="タスク説明")
    category: str = Field(..., description="カテゴリ")
    priority: Optional[str] = Field(None, description="優先度")
    assignee: Optional[str] = Field(None, description="担当者")


class CreateWBSResponse(BaseModel):
    """WBS作成レスポンススキーマ

    MCPプロトコル経由で返却するレスポンスデータ。
    """

    success: bool = Field(..., description="成功フラグ（True: 成功、False: 失敗）")

    registered_tasks: List[TaskSummary] = Field(
        default_factory=list, description="Backlogに登録されたタスクリスト"
    )

    skipped_tasks: List[TaskSummary] = Field(
        default_factory=list, description="重複によりスキップされたタスクリスト"
    )

    error_message: Optional[str] = Field(
        None, description="エラーメッセージ（失敗時のみ）"
    )

    metadata_id: Optional[str] = Field(None, description="保存されたメタデータID")

    master_data_created: int = Field(
        default=0, description="作成されたマスターデータ項目数"
    )

    # 統計情報
    total_registered: int = Field(default=0, description="登録されたタスク総数")

    total_skipped: int = Field(default=0, description="スキップされたタスク総数")

    class Config:
        """Pydantic設定"""

        json_schema_extra = {
            "example": {
                "success": True,
                "registered_tasks": [
                    {
                        "title": "要件定義",
                        "description": "システム要件を定義する",
                        "category": "要件定義",
                        "priority": "高",
                        "assignee": None,
                    }
                ],
                "skipped_tasks": [],
                "error_message": None,
                "metadata_id": "meta_abc123",
                "master_data_created": 3,
                "total_registered": 15,
                "total_skipped": 2,
            }
        }
