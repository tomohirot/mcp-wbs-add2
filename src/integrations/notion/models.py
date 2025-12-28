"""
Notion固有のデータモデル

Notion APIレスポンスに対応するPydanticモデルを定義。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NotionPage(BaseModel):
    """Notionページモデル

    Notion APIから取得したページデータを表現。
    """

    id: str = Field(..., description="ページID（UUID形式）")
    object: str = Field(default="page", description="オブジェクトタイプ")
    created_time: datetime = Field(..., description="作成日時")
    last_edited_time: datetime = Field(..., description="最終編集日時")

    # ページプロパティ
    properties: Dict[str, Any] = Field(..., description="ページプロパティ")

    # 親オブジェクト（データベースまたはページ）
    parent: Dict[str, Any] = Field(..., description="親オブジェクト")

    # URL
    url: str = Field(..., description="NotionページURL")

    # アーカイブ状態
    archived: bool = Field(False, description="アーカイブ済みフラグ")

    # アイコンとカバー
    icon: Optional[Dict[str, Any]] = Field(None, description="ページアイコン")
    cover: Optional[Dict[str, Any]] = Field(None, description="カバー画像")

    class Config:
        """Pydantic設定"""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class NotionDatabase(BaseModel):
    """Notionデータベースモデル

    Notion APIから取得したデータベースデータを表現。
    """

    id: str = Field(..., description="データベースID（UUID形式）")
    object: str = Field(default="database", description="オブジェクトタイプ")
    created_time: datetime = Field(..., description="作成日時")
    last_edited_time: datetime = Field(..., description="最終編集日時")

    # タイトル
    title: List[Dict[str, Any]] = Field(..., description="データベースタイトル")

    # プロパティスキーマ
    properties: Dict[str, Any] = Field(..., description="データベーススキーマ")

    # 親オブジェクト（ページまたはワークスペース）
    parent: Dict[str, Any] = Field(..., description="親オブジェクト")

    # URL
    url: str = Field(..., description="NotionデータベースURL")

    # アーカイブ状態
    archived: bool = Field(False, description="アーカイブ済みフラグ")

    # アイコンとカバー
    icon: Optional[Dict[str, Any]] = Field(None, description="データベースアイコン")
    cover: Optional[Dict[str, Any]] = Field(None, description="カバー画像")

    class Config:
        """Pydantic設定"""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class NotionBlock(BaseModel):
    """Notionブロックモデル

    ページ内のコンテンツブロックを表現。
    """

    id: str = Field(..., description="ブロックID（UUID形式）")
    object: str = Field(default="block", description="オブジェクトタイプ")
    type: str = Field(..., description="ブロックタイプ（paragraph, heading_1, など）")
    created_time: datetime = Field(..., description="作成日時")
    last_edited_time: datetime = Field(..., description="最終編集日時")

    # ブロック固有のコンテンツ（タイプに応じて異なる）
    # 例: paragraph, heading_1, bulleted_list_item, etc.
    content: Optional[Dict[str, Any]] = Field(
        None, description="ブロック固有コンテンツ"
    )

    # 子ブロックの有無
    has_children: bool = Field(False, description="子ブロック有無フラグ")

    # アーカイブ状態
    archived: bool = Field(False, description="アーカイブ済みフラグ")

    class Config:
        """Pydantic設定"""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class NotionUser(BaseModel):
    """Notionユーザーモデル

    Notionワークスペースのユーザーを表現。
    """

    id: str = Field(..., description="ユーザーID（UUID形式）")
    object: str = Field(default="user", description="オブジェクトタイプ")
    type: Optional[str] = Field(None, description="ユーザータイプ（person or bot）")
    name: Optional[str] = Field(None, description="ユーザー名")
    avatar_url: Optional[str] = Field(None, description="アバター画像URL")

    # タイプ固有のプロパティ
    person: Optional[Dict[str, Any]] = Field(None, description="個人ユーザー情報")
    bot: Optional[Dict[str, Any]] = Field(None, description="ボットユーザー情報")


class NotionRichText(BaseModel):
    """Notionリッチテキストモデル

    Notionのリッチテキストコンテンツを表現。
    """

    type: str = Field(..., description="テキストタイプ（text, mention, equation）")
    plain_text: str = Field(..., description="プレーンテキスト")
    href: Optional[str] = Field(None, description="リンクURL")

    # 注釈（太字、イタリックなど）
    annotations: Optional[Dict[str, Any]] = Field(None, description="テキスト注釈")

    # タイプ固有のコンテンツ
    text: Optional[Dict[str, Any]] = Field(None, description="テキストコンテンツ")
    mention: Optional[Dict[str, Any]] = Field(None, description="メンションコンテンツ")
    equation: Optional[Dict[str, Any]] = Field(None, description="数式コンテンツ")
