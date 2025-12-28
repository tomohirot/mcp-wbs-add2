"""
Backlog固有のデータモデル

Backlog APIレスポンスに対応するPydanticモデルを定義。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacklogTask(BaseModel):
    """Backlogタスク（課題）モデル

    Backlog APIから取得した課題データを表現。
    """

    id: int = Field(..., description="課題ID")
    project_id: int = Field(..., description="プロジェクトID")
    issue_key: str = Field(..., description="課題キー（例: PROJ-123）")
    key_id: int = Field(..., description="課題番号")
    summary: str = Field(..., description="件名")
    description: Optional[str] = Field(None, description="詳細")

    # ステータスと種別
    status: Dict[str, Any] = Field(..., description="状態")
    issue_type: Dict[str, Any] = Field(..., description="種別")

    # カテゴリ
    category: Optional[List[Dict[str, Any]]] = Field(None, description="カテゴリリスト")

    # 担当者と優先度
    assignee: Optional[Dict[str, Any]] = Field(None, description="担当者")
    priority: Dict[str, Any] = Field(..., description="優先度")

    # カスタム属性
    custom_fields: Optional[List[Dict[str, Any]]] = Field(
        None, description="カスタム属性リスト"
    )

    # 日時情報
    created: Optional[datetime] = Field(None, description="作成日時")
    updated: Optional[datetime] = Field(None, description="更新日時")

    class Config:
        """Pydantic設定"""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class IssueType(BaseModel):
    """Backlog種別モデル

    課題の種別（課題、リスクなど）を表現。
    """

    id: int = Field(..., description="種別ID")
    project_id: int = Field(..., description="プロジェクトID")
    name: str = Field(..., description="種別名（例: 課題、リスク）")
    color: str = Field(..., description="色コード")
    display_order: int = Field(..., description="表示順")


class Category(BaseModel):
    """Backlogカテゴリモデル

    課題のカテゴリ（事前準備、要件定義など）を表現。
    """

    id: int = Field(..., description="カテゴリID")
    name: str = Field(..., description="カテゴリ名")
    display_order: int = Field(..., description="表示順")


class CustomField(BaseModel):
    """Backlogカスタム属性モデル

    プロジェクトのカスタム属性定義を表現。
    """

    id: int = Field(..., description="カスタム属性ID")
    name: str = Field(..., description="カスタム属性名")
    type_id: int = Field(
        ..., description="属性タイプID（1: 文字列、2: テキスト、など）"
    )
    description: Optional[str] = Field(None, description="説明")
    required: bool = Field(False, description="必須フラグ")

    # タイプ別の追加情報
    applicable_issue_types: Optional[List[int]] = Field(
        None, description="適用可能な種別IDリスト"
    )


class CustomFieldInput(BaseModel):
    """カスタム属性作成用入力モデル

    新しいカスタム属性を作成する際の入力データ。
    """

    name: str = Field(..., min_length=1, description="カスタム属性名")
    type_id: int = Field(
        ..., description="属性タイプID（1: 文字列、2: テキスト、など）"
    )
    description: Optional[str] = Field(None, description="説明")
    required: bool = Field(False, description="必須フラグ")
    applicable_issue_types: Optional[List[int]] = Field(
        None, description="適用可能な種別IDリスト"
    )


class BacklogProject(BaseModel):
    """Backlogプロジェクトモデル

    プロジェクト情報を表現。
    """

    id: int = Field(..., description="プロジェクトID")
    project_key: str = Field(..., description="プロジェクトキー")
    name: str = Field(..., description="プロジェクト名")
    archived: bool = Field(False, description="アーカイブ済みフラグ")
