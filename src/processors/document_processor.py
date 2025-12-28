"""
ドキュメントプロセッサー

Google Document AIを使用したファイル解析機能を提供。
"""

import asyncio

from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai

from ..utils.config import get_config
from ..utils.logger import Logger


class DocumentProcessor:
    """ドキュメント処理クラス

    Google Document AIを使用して各種ファイル形式からテキストを抽出。

    Attributes:
        client: Document AIクライアント
        processor_id: プロセッサーID
        location: リージョン
        logger: ロガーインスタンス
    """

    def __init__(
        self,
        logger: Logger,
        client=None,
        processor_id: str = None,
        location: str = None,
        project_id: str = None,
    ):
        """DocumentProcessorを初期化

        Args:
            logger: ロガーインスタンス
            client: Document AIクライアントインスタンス（テスト用）
            processor_id: プロセッサーID（テスト用）
            location: リージョン（テスト用）
            project_id: GCPプロジェクトID（テスト用）
        """
        self.logger = logger

        if client:
            # テスト用: クライアント直接注入
            self.client = client
            self.processor_id = processor_id or "test-processor"
            self.location = location or "us"
            self.project_id = project_id or "test-project"
        else:
            # 本番用: 設定から初期化
            config = get_config()
            self.processor_id = processor_id or config.document_ai_processor_id
            self.location = location or config.document_ai_location
            self.project_id = project_id or config.gcp_project_id

            # Document AIクライアントの初期化
            opts = ClientOptions(
                api_endpoint=f"{self.location}-documentai.googleapis.com"
            )
            self.client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # タイムアウトとリトライ設定
        self.timeout = 60
        self.max_retries = 3
        self.retry_delay = 2.0

        self.logger.info(
            "Document processor initialized",
            processor_id=self.processor_id,
            location=self.location,
        )

    async def process_file(self, file_content: bytes, mime_type: str) -> str:
        """ファイルをテキストに変換

        Args:
            file_content: ファイルのバイトデータ
            mime_type: MIMEタイプ
                (例: application/pdf, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

        Returns:
            抽出されたテキスト

        Raises:
            Exception: 処理に失敗した場合
        """
        try:
            self.logger.info(
                "Starting document processing",
                mime_type=mime_type,
                size=len(file_content),
            )

            # プロセッサー名を構築
            name = self.client.processor_path(
                self.project_id, self.location, self.processor_id
            )

            # ドキュメントを構築
            raw_document = documentai.RawDocument(
                content=file_content, mime_type=mime_type
            )

            # リクエストを構築
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)

            # 非同期実行（ブロッキングAPIを別スレッドで実行）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.client.process_document, request
            )

            # テキストを抽出
            text = result.document.text

            self.logger.info(
                "Document processing completed",
                extracted_text_length=len(text),
                pages=len(result.document.pages) if result.document.pages else 0,
            )

            return text

        except Exception as e:
            self.logger.error(
                "Failed to process document", error=e, mime_type=mime_type
            )
            raise

    def detect_mime_type(self, file_extension: str) -> str:
        """ファイル拡張子からMIMEタイプを判定

        Args:
            file_extension: ファイル拡張子（例: .pdf, .xlsx）

        Returns:
            MIMEタイプ

        Raises:
            ValueError: サポートされていない拡張子の場合
        """
        mime_types = {
            ".pdf": "application/pdf",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
        }

        ext = file_extension.lower()
        if ext not in mime_types:
            raise ValueError(
                f"サポートされていないファイル形式です: {file_extension}\n"
                f"サポート形式: {', '.join(mime_types.keys())}"
            )

        return mime_types[ext]
