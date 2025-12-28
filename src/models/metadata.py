"""
メタデータモデル

ファイルメタデータのデータ構造を定義。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class FileMetadata(BaseModel):
    """ファイルメタデータモデル

    取得したテンプレートファイルのメタデータを管理。
    Firestoreに保存され、バージョン管理に使用される。

    Attributes:
        id: FirestoreドキュメントID（保存後に設定）
        source_file_name: 取得元ファイル名
        parent_url: 親URL（テンプレートのルートURL）
        file_url: ファイルURL（個別ファイルのURL）
        file_name: ファイル名
        updated_at: 更新日時
        version: バージョン番号（1から始まるインクリメント）
        format: データフォーマット（json または markdown）
        gcs_path: GCS保存パス
    """

    id: Optional[str] = Field(None, description="FirestoreドキュメントID")
    source_file_name: str = Field(..., description="取得元ファイル名")
    parent_url: HttpUrl = Field(..., description="親URL")
    file_url: HttpUrl = Field(..., description="ファイルURL")
    file_name: str = Field(..., description="ファイル名")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")
    version: int = Field(..., ge=1, description="バージョン番号")
    format: str = Field(..., pattern="^(json|markdown)$", description="フォーマット")
    gcs_path: str = Field(..., description="GCS保存パス")

    class Config:
        """Pydantic設定"""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: str,
        }
