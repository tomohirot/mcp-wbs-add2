"""
タスクモデル

WBSタスクのデータ構造を定義。
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import CategoryEnum

# デフォルト値定数
DEFAULT_CATEGORY = CategoryEnum.REQUIREMENTS


class Task(BaseModel):
    """タスクモデル

    WBSのタスク情報を表現するデータモデル。
    テンプレートから取得したタスクと新規タスクの両方に使用。

    Attributes:
        title: タスクのタイトル（必須）
        description: タスクの詳細説明
        category: タスクカテゴリ（デフォルト: 要件定義）
        priority: 優先度（高、中、低）
        assignee: 担当者名
        input: インプット（カスタム属性）
        goal_output: ゴール/アウトプット（カスタム属性）
    """

    title: str = Field(..., min_length=1, description="タスクタイトル")
    description: Optional[str] = Field(None, description="タスク説明")
    category: Optional[CategoryEnum] = Field(default=None, description="タスクカテゴリ")
    priority: Optional[str] = Field(None, description="優先度（高、中、低）")
    assignee: Optional[str] = Field(None, description="担当者")
    input: Optional[str] = Field(None, description="インプット（カスタム属性）")
    goal_output: Optional[str] = Field(
        None, alias="goalOutput", description="ゴール/アウトプット（カスタム属性）"
    )

    class Config:
        """Pydantic設定"""

        use_enum_values = True
        populate_by_name = True
