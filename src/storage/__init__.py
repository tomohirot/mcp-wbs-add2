"""
ストレージパッケージ

Firestore、GCSとの統合とバージョン管理を提供。
"""

from datetime import datetime
from typing import Any, Dict, Optional, Union

from ..models.metadata import FileMetadata
from ..utils.config import get_config
from ..utils.logger import Logger
from .firestore_client import FirestoreClient
from .gcs_client import GCSClient


class StorageManager:
    """ストレージマネージャークラス

    FirestoreとGCSを統合し、バージョン管理機能を提供。

    Attributes:
        firestore_client: Firestoreクライアント
        gcs_client: GCSクライアント
        config: 設定インスタンス
        logger: ロガーインスタンス
    """

    def __init__(
        self, firestore_client: FirestoreClient, gcs_client: GCSClient, logger: Logger
    ):
        """StorageManagerを初期化

        Args:
            firestore_client: Firestoreクライアント
            gcs_client: GCSクライアント
            logger: ロガーインスタンス
        """
        self.firestore_client = firestore_client
        self.gcs_client = gcs_client
        self.config = get_config()
        self.logger = logger

        self.logger.info("Storage manager initialized")

    async def save_data(
        self,
        parent_url: str,
        file_url: str,
        file_name: str,
        data: Union[Dict[str, Any], str],
        format: str,
    ) -> FileMetadata:
        """データとメタデータを保存（バージョン管理付き）

        Args:
            parent_url: 親URL
            file_url: ファイルURL
            file_name: ファイル名
            data: 保存するデータ（DictまたはMarkdown文字列）
            format: フォーマット（json または markdown）

        Returns:
            保存されたメタデータ

        Raises:
            Exception: 保存に失敗した場合
        """
        try:
            self.logger.info(
                "Starting data save operation", file_url=file_url, format=format
            )

            # 最新バージョンを取得してバージョン番号を決定
            latest_metadata = await self.firestore_client.get_latest_metadata(file_url)

            if latest_metadata:
                new_version = latest_metadata.version + 1
            else:
                new_version = 1

            # GCS保存パスを生成
            gcs_path = self.config.get_gcs_path(file_url, new_version)

            # メタデータを作成
            metadata = FileMetadata(
                source_file_name=file_name,
                parent_url=parent_url,
                file_url=file_url,
                file_name=file_name,
                updated_at=datetime.now(),
                version=new_version,
                format=format,
                gcs_path=gcs_path,
            )

            # GCSにデータを保存
            gcs_uri = await self.gcs_client.upload_data(gcs_path, data)

            self.logger.info(
                "Data uploaded to GCS", gcs_uri=gcs_uri, version=new_version
            )

            # Firestoreにメタデータを保存
            doc_id = await self.firestore_client.save_metadata(metadata)
            metadata.id = doc_id

            self.logger.info(
                "Data and metadata saved successfully",
                doc_id=doc_id,
                file_url=file_url,
                version=new_version,
            )

            return metadata

        except Exception as e:
            self.logger.error(
                "Failed to save data and metadata", error=e, file_url=file_url
            )
            raise

    async def get_latest_version(self, file_url: str) -> Optional[FileMetadata]:
        """最新バージョンのメタデータを取得

        Args:
            file_url: ファイルURL

        Returns:
            最新バージョンのメタデータ。存在しない場合はNone
        """
        try:
            metadata = await self.firestore_client.get_latest_metadata(file_url)

            if metadata:
                self.logger.info(
                    "Latest version retrieved",
                    file_url=file_url,
                    version=metadata.version,
                )
            else:
                self.logger.info("No version found", file_url=file_url)

            return metadata

        except Exception as e:
            self.logger.error(
                "Failed to get latest version", error=e, file_url=file_url
            )
            raise

    async def get_data(self, metadata: FileMetadata) -> Union[Dict[str, Any], str]:
        """メタデータを元にGCSからデータを取得

        Args:
            metadata: ファイルメタデータ

        Returns:
            データ（DictまたはMarkdown文字列）

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            # フォーマットに応じてデータを取得
            as_json = metadata.format == "json"

            data = await self.gcs_client.download_data(
                metadata.gcs_path, as_json=as_json
            )

            self.logger.info(
                "Data retrieved from GCS",
                file_url=str(metadata.file_url),
                version=metadata.version,
                format=metadata.format,
            )

            return data

        except Exception as e:
            self.logger.error(
                "Failed to get data from GCS",
                error=e,
                file_url=str(metadata.file_url),
                version=metadata.version,
            )
            raise

    async def get_data_by_version(
        self, file_url: str, version: int
    ) -> Optional[Union[Dict[str, Any], str]]:
        """特定バージョンのデータを取得

        Args:
            file_url: ファイルURL
            version: バージョン番号

        Returns:
            データ（DictまたはMarkdown文字列）。存在しない場合はNone

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            # メタデータを取得
            metadata = await self.firestore_client.get_metadata_by_version(
                file_url, version
            )

            if not metadata:
                self.logger.info(
                    "Version not found", file_url=file_url, version=version
                )
                return None

            # データを取得
            data = await self.get_data(metadata)

            return data

        except Exception as e:
            self.logger.error(
                "Failed to get data by version",
                error=e,
                file_url=file_url,
                version=version,
            )
            raise


__all__ = [
    "StorageManager",
    "FirestoreClient",
    "GCSClient",
]
