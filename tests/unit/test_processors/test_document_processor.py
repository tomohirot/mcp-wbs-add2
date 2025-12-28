"""
Unit tests for DocumentProcessor
"""

from unittest.mock import Mock

import pytest

from src.processors.document_processor import DocumentProcessor


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_document_ai_client():
    """Create mock Document AI client"""
    client = Mock()
    client.processor_path = Mock(
        return_value="projects/test/locations/us/processors/test"
    )
    client.process_document = Mock()
    return client


@pytest.fixture
def document_processor(mock_logger, mock_document_ai_client):
    """Create DocumentProcessor instance with mocked client"""
    return DocumentProcessor(
        mock_logger,
        client=mock_document_ai_client,
        processor_id="test-processor-id",
        location="us",
        project_id="test-project",
    )


class TestDocumentProcessorInit:
    """Tests for DocumentProcessor initialization"""

    def test_init_with_injected_client(self, mock_logger, mock_document_ai_client):
        """Test initialization with injected client"""
        processor = DocumentProcessor(
            mock_logger,
            client=mock_document_ai_client,
            processor_id="my-processor",
            location="asia-northeast1",
            project_id="my-project",
        )
        assert processor.client == mock_document_ai_client
        assert processor.processor_id == "my-processor"
        assert processor.location == "asia-northeast1"
        assert processor.project_id == "my-project"

    def test_init_sets_timeout_and_retry_config(self, document_processor):
        """Test initialization sets timeout and retry configuration"""
        assert document_processor.timeout == 60
        assert document_processor.max_retries == 3
        assert document_processor.retry_delay == 2.0


class TestDocumentProcessorProcessFile:
    """Tests for process_file method"""

    @pytest.mark.asyncio
    async def test_process_pdf_file(self, document_processor, mock_document_ai_client):
        """Test processing PDF file"""
        file_data = b"%PDF-1.4 fake pdf"
        mime_type = "application/pdf"

        # Mock Document AI response
        mock_document = Mock()
        mock_document.text = "Extracted text from PDF"
        mock_document.pages = [Mock(), Mock()]
        mock_response = Mock()
        mock_response.document = mock_document

        mock_document_ai_client.process_document.return_value = mock_response

        result = await document_processor.process_file(file_data, mime_type)

        assert result == "Extracted text from PDF"
        mock_document_ai_client.process_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_excel_file(
        self, document_processor, mock_document_ai_client
    ):
        """Test processing Excel file"""
        file_data = b"fake excel content"
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Mock Document AI response
        mock_document = Mock()
        mock_document.text = "Extracted text from Excel"
        mock_document.pages = []
        mock_response = Mock()
        mock_response.document = mock_document

        mock_document_ai_client.process_document.return_value = mock_response

        result = await document_processor.process_file(file_data, mime_type)

        assert result == "Extracted text from Excel"

    @pytest.mark.asyncio
    async def test_process_word_file(self, document_processor, mock_document_ai_client):
        """Test processing Word file"""
        file_data = b"fake word content"
        mime_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # Mock Document AI response
        mock_document = Mock()
        mock_document.text = "Extracted text from Word"
        mock_document.pages = []
        mock_response = Mock()
        mock_response.document = mock_document

        mock_document_ai_client.process_document.return_value = mock_response

        result = await document_processor.process_file(file_data, mime_type)

        assert result == "Extracted text from Word"

    @pytest.mark.asyncio
    async def test_process_file_failure(
        self, document_processor, mock_document_ai_client
    ):
        """Test processing file failure raises exception"""
        file_data = b"test data"
        mime_type = "application/pdf"

        mock_document_ai_client.process_document.side_effect = Exception(
            "Processing failed"
        )

        with pytest.raises(Exception, match="Processing failed"):
            await document_processor.process_file(file_data, mime_type)


class TestDocumentProcessorDetectMimeType:
    """Tests for detect_mime_type method"""

    def test_detect_pdf_mime_type(self, document_processor):
        """Test detecting PDF MIME type"""
        mime_type = document_processor.detect_mime_type(".pdf")
        assert mime_type == "application/pdf"

    def test_detect_excel_mime_type(self, document_processor):
        """Test detecting Excel MIME type"""
        mime_type = document_processor.detect_mime_type(".xlsx")
        assert (
            mime_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_detect_word_mime_type(self, document_processor):
        """Test detecting Word MIME type"""
        mime_type = document_processor.detect_mime_type(".docx")
        assert (
            mime_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def test_detect_txt_mime_type(self, document_processor):
        """Test detecting text file MIME type"""
        mime_type = document_processor.detect_mime_type(".txt")
        assert mime_type == "text/plain"

    def test_detect_unsupported_extension(self, document_processor):
        """Test unsupported extension raises ValueError"""
        with pytest.raises(ValueError, match="サポートされていないファイル形式です"):
            document_processor.detect_mime_type(".xyz")

    def test_detect_case_insensitive(self, document_processor):
        """Test MIME type detection is case insensitive"""
        mime_type = document_processor.detect_mime_type(".PDF")
        assert mime_type == "application/pdf"
