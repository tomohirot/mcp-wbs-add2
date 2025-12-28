"""
Unit tests for StorageManager
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.models.metadata import FileMetadata
from src.storage import StorageManager


@pytest.fixture
def mock_clients(mock_logger):
    """Create mock Firestore and GCS clients"""
    firestore = Mock()
    gcs = Mock()
    return firestore, gcs, mock_logger


@pytest.fixture
def storage_manager(mock_clients):
    """Create StorageManager with mocks"""
    firestore, gcs, logger = mock_clients
    return StorageManager(firestore, gcs, logger)


class TestStorageManager:
    """Tests for StorageManager class"""

    @pytest.mark.asyncio
    async def test_save_data_new_file(self, storage_manager, mock_clients):
        """Test saving data for new file (version 1)"""
        firestore, gcs, _ = mock_clients

        # Mock get_latest_metadata returns None (no existing versions)
        firestore.get_latest_metadata = AsyncMock(return_value=None)
        firestore.save_metadata = AsyncMock(return_value=Mock(metadata_id="meta123"))
        gcs.upload_data = AsyncMock()

        result = await storage_manager.save_data(
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test_file",
            data={"key": "value"},
            format="json",
        )

        assert result.version == 1
        gcs.upload_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_data_increments_version(self, storage_manager, mock_clients):
        """Test version is incremented for existing file"""
        firestore, gcs, _ = mock_clients

        # Mock existing version 2
        existing_metadata = FileMetadata(
            id="old",
            source_file_name="test.json",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            version=2,
            format="json",
            gcs_path="old/path",
        )
        firestore.get_latest_metadata = AsyncMock(return_value=existing_metadata)
        firestore.save_metadata = AsyncMock(return_value=Mock(metadata_id="meta456"))
        gcs.upload_data = AsyncMock()

        result = await storage_manager.save_data(
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            data={"key": "value"},
            format="json",
        )

        assert result.version == 3  # Incremented from 2 to 3

    @pytest.mark.asyncio
    async def test_get_latest_version(self, storage_manager, mock_clients):
        """Test getting latest version"""
        firestore, _, _ = mock_clients

        metadata = FileMetadata(
            id="meta",
            source_file_name="file.json",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="file",
            version=5,
            format="json",
            gcs_path="path",
        )
        firestore.get_latest_metadata = AsyncMock(return_value=metadata)

        result = await storage_manager.get_latest_version("file_url")
        assert result.version == 5

    @pytest.mark.asyncio
    async def test_get_latest_version_not_found(self, storage_manager, mock_clients):
        """Test getting latest version when not found"""
        firestore, _, _ = mock_clients
        firestore.get_latest_metadata = AsyncMock(return_value=None)

        result = await storage_manager.get_latest_version(
            "https://example.com/notfound"
        )

        assert result is None


class TestStorageManagerGetData:
    """Tests for get_data method"""

    @pytest.fixture
    def mock_firestore_client(self):
        return Mock()

    @pytest.fixture
    def mock_gcs_client(self):
        return Mock()

    @pytest.fixture
    def mock_logger(self):
        logger = Mock()
        logger.info = Mock()
        logger.error = Mock()
        return logger

    @pytest.fixture
    def storage_manager(self, mock_firestore_client, mock_gcs_client, mock_logger):
        return StorageManager(mock_firestore_client, mock_gcs_client, mock_logger)

    @pytest.mark.asyncio
    async def test_get_json_data(self, storage_manager, mock_gcs_client):
        """Test getting JSON data"""
        metadata = FileMetadata(
            source_file_name="test.json",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            version=1,
            format="json",
            gcs_path="path/to/file.json",
        )

        expected_data = {"key": "value"}
        mock_gcs_client.download_data = AsyncMock(return_value=expected_data)

        result = await storage_manager.get_data(metadata)

        assert result == expected_data
        mock_gcs_client.download_data.assert_called_once_with(
            "path/to/file.json", as_json=True
        )

    @pytest.mark.asyncio
    async def test_get_markdown_data(self, storage_manager, mock_gcs_client):
        """Test getting Markdown data"""
        metadata = FileMetadata(
            source_file_name="test.md",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            version=1,
            format="markdown",
            gcs_path="path/to/file.md",
        )

        expected_data = "# Markdown content"
        mock_gcs_client.download_data = AsyncMock(return_value=expected_data)

        result = await storage_manager.get_data(metadata)

        assert result == expected_data
        mock_gcs_client.download_data.assert_called_once_with(
            "path/to/file.md", as_json=False
        )

    @pytest.mark.asyncio
    async def test_get_data_failure(self, storage_manager, mock_gcs_client):
        """Test get_data raises exception on failure"""
        metadata = FileMetadata(
            source_file_name="test.json",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            version=1,
            format="json",
            gcs_path="path/to/file.json",
        )

        mock_gcs_client.download_data = AsyncMock(
            side_effect=Exception("Download failed")
        )

        with pytest.raises(Exception, match="Download failed"):
            await storage_manager.get_data(metadata)


class TestStorageManagerGetDataByVersion:
    """Tests for get_data_by_version method"""

    @pytest.fixture
    def mock_firestore_client(self):
        return Mock()

    @pytest.fixture
    def mock_gcs_client(self):
        return Mock()

    @pytest.fixture
    def mock_logger(self):
        logger = Mock()
        logger.info = Mock()
        logger.error = Mock()
        return logger

    @pytest.fixture
    def storage_manager(self, mock_firestore_client, mock_gcs_client, mock_logger):
        return StorageManager(mock_firestore_client, mock_gcs_client, mock_logger)

    @pytest.mark.asyncio
    async def test_get_data_by_version_found(
        self, storage_manager, mock_firestore_client, mock_gcs_client
    ):
        """Test getting data by specific version"""
        metadata = FileMetadata(
            source_file_name="test.json",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            version=2,
            format="json",
            gcs_path="path/to/file/v2.json",
        )

        expected_data = {"version": 2, "data": "test"}
        mock_firestore_client.get_metadata_by_version = AsyncMock(return_value=metadata)
        mock_gcs_client.download_data = AsyncMock(return_value=expected_data)

        result = await storage_manager.get_data_by_version(
            "https://example.com/file", 2
        )

        assert result == expected_data
        mock_firestore_client.get_metadata_by_version.assert_called_once_with(
            "https://example.com/file", 2
        )

    @pytest.mark.asyncio
    async def test_get_data_by_version_not_found(
        self, storage_manager, mock_firestore_client
    ):
        """Test getting data by version when version doesn't exist"""
        mock_firestore_client.get_metadata_by_version = AsyncMock(return_value=None)

        result = await storage_manager.get_data_by_version(
            "https://example.com/file", 99
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_data_by_version_failure(
        self, storage_manager, mock_firestore_client
    ):
        """Test get_data_by_version raises exception on failure"""
        mock_firestore_client.get_metadata_by_version = AsyncMock(
            side_effect=Exception("Metadata retrieval failed")
        )

        with pytest.raises(Exception, match="Metadata retrieval failed"):
            await storage_manager.get_data_by_version("https://example.com/file", 1)
