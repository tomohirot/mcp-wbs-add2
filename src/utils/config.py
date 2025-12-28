"""
設定管理ユーティリティ

環境変数と設定ファイルからの設定読み込みを提供。
"""

import os
from typing import Optional


class Config:
    """設定管理クラス（シングルトン）

    環境変数と設定ファイルから設定を読み込み、
    アプリケーション全体で共有する。
    """

    _instance: Optional["Config"] = None

    def __new__(cls) -> "Config":
        """シングルトンインスタンスを返却"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """設定を初期化"""
        if self._initialized:
            return

        # GCP設定
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID", "")
        self.gcs_bucket = os.getenv("GCS_BUCKET", "wbs-templates")
        self.firestore_collection = os.getenv("FIRESTORE_COLLECTION", "file_metadata")

        # Backlog設定
        self.backlog_api_key = os.getenv("BACKLOG_API_KEY", "")
        self.backlog_space_url = os.getenv("BACKLOG_SPACE_URL", "")

        # Notion設定
        self.notion_api_key = os.getenv("NOTION_API_KEY", "")

        # Document AI設定
        self.document_ai_processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID", "")
        self.document_ai_location = os.getenv("DOCUMENT_AI_LOCATION", "us")

        # アプリケーション設定
        self.default_category = os.getenv("DEFAULT_CATEGORY", "要件定義")
        self.max_retry_count = int(os.getenv("MAX_RETRY_COUNT", "3"))
        self.api_timeout = int(os.getenv("API_TIMEOUT", "30"))

        self._initialized = True

    def validate(self) -> bool:
        """必須設定の存在を確認

        Returns:
            すべての必須設定が存在する場合True
        """
        required_fields = [
            self.gcp_project_id,
            self.backlog_api_key,
        ]

        return all(field for field in required_fields)

    def get_gcs_path(self, file_url: str, version: int) -> str:
        """GCS保存パスを生成

        Args:
            file_url: ファイルURL
            version: バージョン番号

        Returns:
            GCS保存パス
        """
        # URLからハッシュを生成してパス化
        from hashlib import sha256

        url_hash = sha256(file_url.encode()).hexdigest()[:16]
        return f"templates/{url_hash}/v{version}"


def get_config() -> Config:
    """Configインスタンスを取得（シングルトン）

    Returns:
        Configインスタンス
    """
    return Config()
