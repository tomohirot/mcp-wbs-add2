"""
Unit tests for FirestoreClient
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.metadata import FileMetadata
from src.storage.firestore_client import FirestoreClient


class AsyncIterator:
    """Helper class for async iteration in tests"""

    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


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
def mock_db():
    """Create mock Firestore database"""
    return Mock()


@pytest.fixture
def firestore_client(mock_db, mock_logger):
    """Create FirestoreClient instance with mocked db"""
    return FirestoreClient(mock_logger, db=mock_db, collection_name="test_metadata")


class TestFirestoreClientInit:
    """Tests for FirestoreClient initialization"""

    def test_init_with_injected_db(self, mock_logger, mock_db):
        """Test initialization with injected database"""
        client = FirestoreClient(mock_logger, db=mock_db, collection_name="custom")
        assert client.db == mock_db
        assert client.collection_name == "custom"

    def test_init_default_collection_name(self, mock_logger, mock_db):
        """Test default collection name when injected"""
        client = FirestoreClient(mock_logger, db=mock_db)
        assert client.collection_name == "test_metadata"


class TestFirestoreClientSaveMetadata:
    """Tests for save_metadata method"""

    @pytest.mark.asyncio
    async def test_save_metadata_new(self, firestore_client, mock_db):
        """Test saving new metadata"""
        metadata = FileMetadata(
            source_file_name="test.json",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            version=1,
            format="json",
            gcs_path="path/to/file",
        )

        # Mock Firestore collection and document
        mock_doc_ref = Mock()
        mock_doc_ref.id = "new_doc_123"
        mock_collection = Mock()
        mock_collection.add = AsyncMock(return_value=(Mock(), mock_doc_ref))
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.save_metadata(metadata)

        assert result == "new_doc_123"
        mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_metadata_update_existing(self, firestore_client, mock_db):
        """Test updating existing metadata"""
        metadata = FileMetadata(
            id="existing_123",
            source_file_name="test.json",
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            version=2,
            format="json",
            gcs_path="path/to/file",
        )

        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.set = AsyncMock()
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.save_metadata(metadata)

        assert result == "existing_123"
        mock_doc.set.assert_called_once()


class TestFirestoreClientGetLatestMetadata:
    """Tests for get_latest_metadata method"""

    @pytest.mark.asyncio
    async def test_get_latest_metadata_found(self, firestore_client, mock_db):
        """Test getting latest metadata when exists"""
        # Mock query result
        mock_doc = Mock()
        mock_doc.id = "doc_123"
        mock_doc.to_dict.return_value = {
            "source_file_name": "test.json",
            "parent_url": "https://example.com",
            "file_url": "https://example.com/file",
            "file_name": "test",
            "version": 3,
            "format": "json",
            "gcs_path": "path/to/file",
            "updated_at": datetime.now(),
        }

        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = AsyncIterator([mock_doc])

        mock_collection = Mock()
        mock_collection.where.return_value.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.get_latest_metadata("https://example.com/file")

        assert result is not None
        assert result.id == "doc_123"
        assert result.version == 3

    @pytest.mark.asyncio
    async def test_get_latest_metadata_not_found(self, firestore_client, mock_db):
        """Test getting latest metadata when not exists"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = AsyncIterator([])

        mock_collection = Mock()
        mock_collection.where.return_value.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.get_latest_metadata(
            "https://example.com/notfound"
        )

        assert result is None


class TestFirestoreClientGetMetadataByVersion:
    """Tests for get_metadata_by_version method"""

    @pytest.mark.asyncio
    async def test_get_metadata_by_version_found(self, firestore_client, mock_db):
        """Test getting metadata by specific version"""
        # Mock query result
        mock_doc = Mock()
        mock_doc.id = "doc_456"
        mock_doc.to_dict.return_value = {
            "source_file_name": "test.json",
            "parent_url": "https://example.com",
            "file_url": "https://example.com/file",
            "file_name": "test",
            "version": 2,
            "format": "json",
            "gcs_path": "path/to/file/v2",
            "updated_at": datetime.now(),
        }

        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = AsyncIterator([mock_doc])

        mock_collection = Mock()
        mock_collection.where.return_value.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.get_metadata_by_version(
            "https://example.com/file", 2
        )

        assert result is not None
        assert result.id == "doc_456"
        assert result.version == 2

    @pytest.mark.asyncio
    async def test_get_metadata_by_version_not_found(self, firestore_client, mock_db):
        """Test getting metadata when version not found"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = AsyncIterator([])

        mock_collection = Mock()
        mock_collection.where.return_value.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.get_metadata_by_version(
            "https://example.com/file", 99
        )

        assert result is None


class TestFirestoreClientGetAllVersions:
    """Tests for get_all_versions method"""

    @pytest.mark.asyncio
    async def test_get_all_versions_multiple(self, firestore_client, mock_db):
        """Test getting all versions of a file"""
        # Mock query results with multiple versions
        mock_docs = []
        for version in [3, 2, 1]:
            mock_doc = Mock()
            mock_doc.id = f"doc_v{version}"
            mock_doc.to_dict.return_value = {
                "source_file_name": "test.json",
                "parent_url": "https://example.com",
                "file_url": "https://example.com/file",
                "file_name": "test",
                "version": version,
                "format": "json",
                "gcs_path": f"path/to/file/v{version}",
                "updated_at": datetime.now(),
            }
            mock_docs.append(mock_doc)

        mock_query = Mock()
        mock_query.stream.return_value = AsyncIterator(mock_docs)

        mock_collection = Mock()
        mock_collection.where.return_value.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.get_all_versions("https://example.com/file")

        assert len(result) == 3
        assert result[0].version == 3
        assert result[1].version == 2
        assert result[2].version == 1

    @pytest.mark.asyncio
    async def test_get_all_versions_empty(self, firestore_client, mock_db):
        """Test getting all versions when none exist"""
        mock_query = Mock()
        mock_query.stream.return_value = AsyncIterator([])

        mock_collection = Mock()
        mock_collection.where.return_value.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = await firestore_client.get_all_versions("https://example.com/file")

        assert result == []


class TestFirestoreClientClose:
    """Tests for close method"""

    @pytest.mark.asyncio
    async def test_close(self, firestore_client):
        """Test closing Firestore client"""
        await firestore_client.close()
        # Just verify it doesn't raise an exception
