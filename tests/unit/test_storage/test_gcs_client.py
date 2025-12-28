"""
Unit tests for GCSClient
"""

import json
from unittest.mock import Mock

import pytest

from src.storage.gcs_client import GCSClient


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
def mock_bucket():
    """Create mock GCS bucket"""
    bucket = Mock()
    bucket.name = "test-bucket"
    return bucket


@pytest.fixture
def gcs_client(mock_logger, mock_bucket):
    """Create GCSClient instance with mocked bucket"""
    return GCSClient(mock_logger, bucket=mock_bucket)


class TestGCSClientInit:
    """Tests for GCSClient initialization"""

    def test_init_with_injected_bucket(self, mock_logger, mock_bucket):
        """Test initialization with injected bucket"""
        client = GCSClient(mock_logger, bucket=mock_bucket)
        assert client.bucket == mock_bucket
        assert client.bucket_name == "test-bucket"

    def test_init_sets_retry_config(self, gcs_client):
        """Test initialization sets retry configuration"""
        assert gcs_client.max_retries == 3
        assert gcs_client.retry_delay == 1.0


class TestGCSClientUploadData:
    """Tests for upload_data method"""

    @pytest.mark.asyncio
    async def test_upload_json_data(self, gcs_client, mock_bucket):
        """Test uploading JSON data"""
        data = {"key": "value", "number": 123}
        path = "test/path/file.json"

        mock_blob = Mock()
        mock_blob.upload_from_string = Mock()
        mock_bucket.blob.return_value = mock_blob

        await gcs_client.upload_data(path, data)

        # Verify blob was created with correct path
        mock_bucket.blob.assert_called_once_with(path)

        # Verify upload was called with JSON string
        args = mock_blob.upload_from_string.call_args
        uploaded_data = args[0][0]
        assert json.loads(uploaded_data) == data

    @pytest.mark.asyncio
    async def test_upload_string_data(self, gcs_client, mock_bucket):
        """Test uploading string data"""
        data = "Plain text content"
        path = "test/path/file.txt"

        mock_blob = Mock()
        mock_blob.upload_from_string = Mock()
        mock_bucket.blob.return_value = mock_blob

        await gcs_client.upload_data(path, data)

        # Verify upload was called with string
        args = mock_blob.upload_from_string.call_args
        uploaded_data = args[0][0]
        assert uploaded_data == data

    @pytest.mark.asyncio
    async def test_upload_with_content_type(self, gcs_client, mock_bucket):
        """Test upload sets correct content type"""
        mock_blob = Mock()
        mock_blob.upload_from_string = Mock()
        mock_bucket.blob.return_value = mock_blob

        await gcs_client.upload_data("file.json", {"test": "data"})

        # Verify content_type was set
        args = mock_blob.upload_from_string.call_args
        assert args[1]["content_type"] == "application/json"

    @pytest.mark.asyncio
    async def test_upload_failure(self, gcs_client, mock_bucket):
        """Test upload raises exception on failure"""
        mock_blob = Mock()
        mock_blob.upload_from_string = Mock(side_effect=Exception("Upload failed"))
        mock_bucket.blob.return_value = mock_blob

        with pytest.raises(Exception, match="Upload failed"):
            await gcs_client.upload_data("test.json", {"data": "test"})


class TestGCSClientDownloadData:
    """Tests for download_data method"""

    @pytest.mark.asyncio
    async def test_download_json_data(self, gcs_client, mock_bucket):
        """Test downloading JSON data"""
        test_data = {"key": "value"}
        json_string = json.dumps(test_data)

        mock_blob = Mock()
        mock_blob.download_as_bytes = Mock(return_value=json_string.encode("utf-8"))
        mock_bucket.blob.return_value = mock_blob

        result = await gcs_client.download_data("test/file.json")

        assert result == test_data
        mock_blob.download_as_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_text_data(self, gcs_client, mock_bucket):
        """Test downloading text data"""
        text_data = "Plain text content"

        mock_blob = Mock()
        mock_blob.download_as_bytes = Mock(return_value=text_data.encode("utf-8"))
        mock_bucket.blob.return_value = mock_blob

        result = await gcs_client.download_data("test/file.txt", as_json=False)

        assert result == text_data

    @pytest.mark.asyncio
    async def test_download_nonexistent_file(self, gcs_client, mock_bucket):
        """Test downloading nonexistent file"""
        mock_blob = Mock()
        mock_blob.download_as_bytes = Mock(side_effect=Exception("File not found"))
        mock_bucket.blob.return_value = mock_blob

        with pytest.raises(Exception):
            await gcs_client.download_data("nonexistent.json")


class TestGCSClientFileExists:
    """Tests for file_exists method"""

    @pytest.mark.asyncio
    async def test_file_exists_true(self, gcs_client, mock_bucket):
        """Test file exists returns True"""
        mock_blob = Mock()
        mock_blob.exists = Mock(return_value=True)
        mock_bucket.blob.return_value = mock_blob

        result = await gcs_client.file_exists("existing_file.json")

        assert result is True

    @pytest.mark.asyncio
    async def test_file_exists_false(self, gcs_client, mock_bucket):
        """Test file exists returns False"""
        mock_blob = Mock()
        mock_blob.exists = Mock(return_value=False)
        mock_bucket.blob.return_value = mock_blob

        result = await gcs_client.file_exists("nonexistent.json")

        assert result is False


class TestGCSClientDeleteFile:
    """Tests for delete_file method"""

    @pytest.mark.asyncio
    async def test_delete_file(self, gcs_client, mock_bucket):
        """Test deleting file"""
        mock_blob = Mock()
        mock_blob.delete = Mock()
        mock_bucket.blob.return_value = mock_blob

        await gcs_client.delete_file("file_to_delete.json")

        mock_blob.delete.assert_called_once()
