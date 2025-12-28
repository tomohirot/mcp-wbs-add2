"""
GCS（Google Cloud Storage）クライアント

データファイルのアップロード・ダウンロードを提供。
"""

import asyncio
import json
from functools import partial
from typing import Any, Dict, Union

from google.cloud import storage

from ..utils.config import get_config
from ..utils.logger import Logger


class GCSClient:
    """GCSクライアントクラス

    JSON/Markdownファイルのアップロード・ダウンロード機能を提供。

    Attributes:
        client: GCSクライアント
        bucket_name: バケット名
        logger: ロガーインスタンス
    """

    def __init__(self, logger: Logger, bucket=None, client=None):
        """GCSClientを初期化

        Args:
            logger: ロガーインスタンス
            bucket: GCSバケットインスタンス（テスト用）
            client: GCSクライアントインスタンス（テスト用）
        """
        self.logger = logger

        if bucket:
            # テスト用: バケット直接注入
            self.bucket = bucket
            self.bucket_name = getattr(bucket, "name", "test-bucket")
        else:
            # 本番用: クライアントとバケット名から初期化
            config = get_config()
            self.bucket_name = config.gcs_bucket

            if client:
                self.client = client
            else:
                self.client = storage.Client(project=config.gcp_project_id)

            self.bucket = self.client.bucket(self.bucket_name)

        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 1.0

        self.logger.info("GCS client initialized", bucket=self.bucket_name)

    async def upload_data(
        self,
        path: str,
        data: Union[Dict[str, Any], str],
        content_type: str = "application/json",
    ) -> str:
        """データをGCSにアップロード

        Args:
            path: GCS内のパス
            data: アップロードするデータ（DictまたはMarkdown文字列）
            content_type: コンテンツタイプ（デフォルト: application/json）

        Returns:
            アップロードされたGCS URI

        Raises:
            Exception: アップロードに失敗した場合
        """
        try:
            blob = self.bucket.blob(path)

            # データを文字列に変換
            if isinstance(data, dict):
                content = json.dumps(data, ensure_ascii=False, indent=2)
                content_type = "application/json"
            else:
                content = data
                content_type = "text/markdown"

            # 非同期実行（ブロッキングIOを別スレッドで実行）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                partial(blob.upload_from_string, content, content_type=content_type),
            )

            gcs_uri = f"gs://{self.bucket_name}/{path}"

            self.logger.info(
                "Data uploaded to GCS",
                path=path,
                gcs_uri=gcs_uri,
                content_type=content_type,
                size=len(content),
            )

            return gcs_uri

        except Exception as e:
            self.logger.error("Failed to upload data to GCS", error=e, path=path)
            raise

    async def download_data(
        self, path: str, as_json: bool = True
    ) -> Union[Dict[str, Any], str]:
        """GCSからデータをダウンロード

        Args:
            path: GCS内のパス
            as_json: JSONとしてパースする場合True

        Returns:
            ダウンロードしたデータ（Dict または Markdown文字列）

        Raises:
            Exception: ダウンロードに失敗した場合
        """
        try:
            blob = self.bucket.blob(path)

            # 非同期実行（ブロッキングIOを別スレッドで実行）
            loop = asyncio.get_event_loop()
            content_bytes = await loop.run_in_executor(None, blob.download_as_bytes)

            content = content_bytes.decode("utf-8")

            # JSONパースまたは文字列として返却
            if as_json:
                data = json.loads(content)
            else:
                data = content

            self.logger.info(
                "Data downloaded from GCS",
                path=path,
                as_json=as_json,
                size=len(content),
            )

            return data

        except Exception as e:
            self.logger.error("Failed to download data from GCS", error=e, path=path)
            raise

    async def file_exists(self, path: str) -> bool:
        """ファイルの存在確認

        Args:
            path: GCS内のパス

        Returns:
            ファイルが存在する場合True
        """
        try:
            blob = self.bucket.blob(path)

            # 非同期実行
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(None, blob.exists)

            self.logger.debug("File existence checked", path=path, exists=exists)

            return exists

        except Exception as e:
            self.logger.error(
                "Failed to check file existence in GCS", error=e, path=path
            )
            raise

    async def delete_file(self, path: str) -> None:
        """ファイルを削除

        Args:
            path: GCS内のパス

        Raises:
            Exception: 削除に失敗した場合
        """
        try:
            blob = self.bucket.blob(path)

            # 非同期実行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob.delete)

            self.logger.info("File deleted from GCS", path=path)

        except Exception as e:
            self.logger.error("Failed to delete file from GCS", error=e, path=path)
            raise
