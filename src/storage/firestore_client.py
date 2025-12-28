"""
Firestoreクライアント

ファイルメタデータのCRUD操作とバージョン管理を提供。
"""

from typing import List, Optional

from google.cloud import firestore

from ..models.metadata import FileMetadata
from ..utils.config import get_config
from ..utils.logger import Logger


class FirestoreClient:
    """Firestoreクライアントクラス

    ファイルメタデータのCRUD操作を提供し、バージョン管理を実現。

    Attributes:
        db: Firestoreクライアント
        collection_name: コレクション名
        logger: ロガーインスタンス
    """

    def __init__(self, logger: Logger, db=None, collection_name: str = None):
        """FirestoreClientを初期化

        Args:
            logger: ロガーインスタンス
            db: Firestoreクライアントインスタンス（テスト用）
            collection_name: コレクション名（テスト用）
        """
        self.logger = logger

        if db:
            # テスト用: クライアント直接注入
            self.db = db
            self.collection_name = collection_name or "test_metadata"
        else:
            # 本番用: 設定から初期化
            config = get_config()
            self.collection_name = collection_name or config.firestore_collection
            self.db = firestore.AsyncClient(project=config.gcp_project_id)

        self.logger.info(
            "Firestore client initialized", collection=self.collection_name
        )

    async def save_metadata(self, metadata: FileMetadata) -> str:
        """メタデータをFirestoreに保存

        Args:
            metadata: 保存するメタデータ

        Returns:
            保存されたドキュメントID

        Raises:
            Exception: 保存に失敗した場合
        """
        try:
            # メタデータをdict形式に変換
            data = metadata.model_dump(mode="json", exclude={"id"})

            collection_ref = self.db.collection(self.collection_name)

            if metadata.id:
                # 既存ドキュメントの更新
                doc_ref = collection_ref.document(metadata.id)
                await doc_ref.set(data)
                doc_id = metadata.id
            else:
                # 新規ドキュメントの作成
                _, doc_ref = await collection_ref.add(data)
                doc_id = doc_ref.id

            self.logger.info(
                "Metadata saved to Firestore",
                doc_id=doc_id,
                file_url=str(metadata.file_url),
                version=metadata.version,
            )

            return doc_id

        except Exception as e:
            self.logger.error(
                "Failed to save metadata to Firestore",
                error=e,
                file_url=str(metadata.file_url),
            )
            raise

    async def get_latest_metadata(self, file_url: str) -> Optional[FileMetadata]:
        """最新バージョンのメタデータを取得

        Args:
            file_url: ファイルURL

        Returns:
            最新バージョンのメタデータ。存在しない場合はNone

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            collection_ref = self.db.collection(self.collection_name)

            # file_urlでフィルタし、versionで降順ソート、最初の1件を取得
            query = (
                collection_ref.where("file_url", "==", file_url)
                .order_by("version", direction=firestore.Query.DESCENDING)
                .limit(1)
            )

            docs = [doc async for doc in query.stream()]

            if not docs:
                self.logger.info("No metadata found for file_url", file_url=file_url)
                return None

            doc = docs[0]
            data = doc.to_dict()
            data["id"] = doc.id

            metadata = FileMetadata(**data)

            self.logger.info(
                "Latest metadata retrieved",
                doc_id=doc.id,
                file_url=file_url,
                version=metadata.version,
            )

            return metadata

        except Exception as e:
            self.logger.error(
                "Failed to get latest metadata from Firestore",
                error=e,
                file_url=file_url,
            )
            raise

    async def get_metadata_by_version(
        self, file_url: str, version: int
    ) -> Optional[FileMetadata]:
        """特定バージョンのメタデータを取得

        Args:
            file_url: ファイルURL
            version: バージョン番号

        Returns:
            指定バージョンのメタデータ。存在しない場合はNone

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            collection_ref = self.db.collection(self.collection_name)

            # file_urlとversionでフィルタ
            query = (
                collection_ref.where("file_url", "==", file_url)
                .where("version", "==", version)
                .limit(1)
            )

            docs = [doc async for doc in query.stream()]

            if not docs:
                self.logger.info(
                    "No metadata found for file_url and version",
                    file_url=file_url,
                    version=version,
                )
                return None

            doc = docs[0]
            data = doc.to_dict()
            data["id"] = doc.id

            metadata = FileMetadata(**data)

            self.logger.info(
                "Metadata retrieved by version",
                doc_id=doc.id,
                file_url=file_url,
                version=version,
            )

            return metadata

        except Exception as e:
            self.logger.error(
                "Failed to get metadata by version from Firestore",
                error=e,
                file_url=file_url,
                version=version,
            )
            raise

    async def get_all_versions(self, file_url: str) -> List[FileMetadata]:
        """ファイルURLの全バージョンを取得

        Args:
            file_url: ファイルURL

        Returns:
            全バージョンのメタデータリスト（バージョン降順）

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            collection_ref = self.db.collection(self.collection_name)

            # file_urlでフィルタし、versionで降順ソート
            query = collection_ref.where("file_url", "==", file_url).order_by(
                "version", direction=firestore.Query.DESCENDING
            )

            docs = [doc async for doc in query.stream()]

            metadata_list = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                metadata_list.append(FileMetadata(**data))

            self.logger.info(
                "All versions retrieved",
                file_url=file_url,
                version_count=len(metadata_list),
            )

            return metadata_list

        except Exception as e:
            self.logger.error(
                "Failed to get all versions from Firestore", error=e, file_url=file_url
            )
            raise

    async def close(self) -> None:
        """Firestoreクライアントをクローズ"""
        # AsyncClientはクローズ不要だが、将来の拡張のためにメソッドを用意
        self.logger.info("Firestore client closed")
