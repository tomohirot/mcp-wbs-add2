"""
End-to-end integration tests for WBS creation flow
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.integrations.backlog.client import BacklogMCPClient
from src.integrations.mcp_factory import MCPFactory
from src.mcp.handlers import handle_create_wbs
from src.mcp.schemas import CreateWBSRequest
from src.models.enums import CategoryEnum, ServiceType
from src.models.task import Task
from src.processors.converter import Converter
from src.processors.url_parser import URLParser
from src.services.category_detector import CategoryDetector
from src.services.master_service import MasterService
from src.services.task_merger import TaskMerger
from src.services.wbs_service import WBSService
from src.storage import StorageManager


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_wbs_creation_flow(mock_logger):
    """Test complete WBS creation workflow from request to response"""
    # Create request
    request = CreateWBSRequest(
        template_url="https://test.backlog.com/view/PROJ-1",
        new_tasks_text="- New task 1 | priority: high",
        project_key="PROJ",
    )

    # Mock WBS service
    mock_wbs_service = Mock()
    mock_wbs_service.create_wbs = AsyncMock(
        return_value=Mock(
            success=True,
            registered_tasks=[],
            skipped_tasks=[],
            error_message=None,
            metadata_id="test123",
            master_data_created=3,
        )
    )

    # Execute handler
    response = await handle_create_wbs(request, mock_wbs_service, mock_logger)

    # Verify
    assert response.success is True
    assert response.master_data_created == 3
    mock_wbs_service.create_wbs.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_integration_flow(mock_logger):
    """Test integration of multiple services together"""
    # Create real service instances with mocked external dependencies
    mock_backlog_client = Mock()
    mock_backlog_client.fetch_data = AsyncMock(return_value={})
    mock_backlog_client.get_tasks = AsyncMock(return_value=[])
    mock_backlog_client.create_tasks = AsyncMock(return_value=[])

    mock_storage = Mock()
    mock_storage.save_data = AsyncMock(return_value=Mock(id="meta123", version=1))

    # Real converters and parsers
    converter = Converter()
    url_parser = URLParser()
    category_detector = CategoryDetector()
    task_merger = TaskMerger(category_detector, mock_logger)

    # Master service with mocked Backlog client
    master_service = MasterService(mock_backlog_client, mock_logger)
    master_service.setup_master_data = AsyncMock(
        return_value=Mock(success=True, total_created=0, errors=[])
    )

    # Mock factory that returns our mock client
    mock_factory = Mock()
    mock_factory.create_client = Mock(return_value=mock_backlog_client)

    # Create WBS service with all dependencies
    wbs_service = WBSService(
        master_service=master_service,
        url_parser=url_parser,
        mcp_factory=mock_factory,
        document_processor=Mock(),
        converter=converter,
        task_merger=task_merger,
        backlog_client=mock_backlog_client,
        storage_manager=mock_storage,
        logger=mock_logger,
    )

    # Execute WBS creation
    result = await wbs_service.create_wbs(
        template_url="https://test.backlog.com/view/PROJ-1",
        new_tasks_text="- タスク1 | category: 実装 | priority: 高",
        project_key="PROJ",
    )

    # Verify
    assert result.success is True
    mock_storage.save_data.assert_called_once()
    master_service.setup_master_data.assert_called_once()


@pytest.mark.integration
class TestBacklogIntegration:
    """Tests for Backlog client integration"""

    @pytest.mark.asyncio
    async def test_backlog_client_initialization(self, mock_logger):
        """Test Backlog client can be initialized"""
        client = BacklogMCPClient(
            api_key="test-key", space_url="https://test.backlog.com", logger=mock_logger
        )

        assert client.api_key == "test-key"
        assert client.space_url == "https://test.backlog.com"
        assert client.logger == mock_logger

    @pytest.mark.asyncio
    async def test_backlog_client_with_mcp_factory(self, mock_logger):
        """Test creating Backlog client via MCPFactory"""
        with patch("src.integrations.mcp_factory.get_config") as mock_config:
            mock_config.return_value = Mock(
                backlog_api_key="test-key",
                backlog_space_url="https://test.backlog.com",
            )

            factory = MCPFactory(mock_logger)
            client = factory.create_client(ServiceType.BACKLOG)

            assert isinstance(client, BacklogMCPClient)
            assert client.api_key == "test-key"


@pytest.mark.integration
class TestStorageIntegration:
    """Tests for storage integration"""

    @pytest.mark.asyncio
    async def test_storage_manager_initialization(self, mock_logger):
        """Test storage manager can be initialized"""
        mock_firestore = Mock()
        mock_gcs = Mock()

        storage = StorageManager(mock_firestore, mock_gcs, mock_logger)

        assert storage.firestore_client == mock_firestore
        assert storage.gcs_client == mock_gcs
        assert storage.logger == mock_logger

    @pytest.mark.asyncio
    async def test_storage_save_and_retrieve_flow(self, mock_logger):
        """Test saving and retrieving data"""
        mock_firestore = Mock()
        mock_gcs = Mock()

        # Mock save flow
        mock_firestore.get_latest_metadata = AsyncMock(return_value=None)
        mock_firestore.save_metadata = AsyncMock(return_value="meta123")
        mock_gcs.upload_data = AsyncMock()

        storage = StorageManager(mock_firestore, mock_gcs, mock_logger)

        result = await storage.save_data(
            parent_url="https://example.com",
            file_url="https://example.com/file",
            file_name="test",
            data={"key": "value"},
            format="json",
        )

        # Verify
        assert result.version == 1
        mock_gcs.upload_data.assert_called_once()
        mock_firestore.save_metadata.assert_called_once()


@pytest.mark.integration
class TestConverterIntegration:
    """Tests for converter integration"""

    def test_converter_with_task_merger(self, mock_logger):
        """Test converter output works with task merger"""
        converter = Converter()
        category_detector = CategoryDetector()
        task_merger = TaskMerger(category_detector, mock_logger)

        # Parse tasks from text
        text = """
- 要件定義タスク | category: 要件定義 | priority: 高
- 実装タスク | category: 実装 | priority: 中
- テストタスク | category: テスト | priority: 低
"""
        tasks = converter.parse_tasks_from_text(text)

        # Merge with empty list
        merged = task_merger.merge_tasks(tasks, [])

        # Verify tasks are in category order
        assert len(merged) == 3
        assert merged[0].category == CategoryEnum.REQUIREMENTS
        assert merged[1].category == CategoryEnum.IMPLEMENTATION
        assert merged[2].category == CategoryEnum.TESTING

    def test_category_detection_integration(self):
        """Test category detection with task creation"""
        converter = Converter()
        detector = CategoryDetector()

        # Create tasks without category
        text = """
- 要件をまとめる
- システムを実装する
- テストを実施する
"""
        tasks = converter.parse_tasks_from_text(text)

        # Detect categories
        for task in tasks:
            if not task.category:
                category = detector.detect_category(task)
                task.category = category

        # Verify categories were detected
        assert tasks[0].category == CategoryEnum.REQUIREMENTS
        assert tasks[1].category == CategoryEnum.IMPLEMENTATION
        assert tasks[2].category == CategoryEnum.TESTING


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Tests for error handling across services"""

    @pytest.mark.asyncio
    async def test_wbs_service_handles_storage_error(self, mock_logger):
        """Test WBS service handles storage errors gracefully"""
        mock_storage = Mock()
        mock_storage.save_data = AsyncMock(side_effect=Exception("Storage failed"))

        mock_backlog = Mock()
        mock_backlog.get_tasks = AsyncMock(return_value=[])

        category_detector = CategoryDetector()
        wbs_service = WBSService(
            master_service=Mock(
                setup_master_data=AsyncMock(
                    return_value=Mock(success=True, total_created=0, errors=[])
                )
            ),
            url_parser=URLParser(),
            mcp_factory=Mock(create_client=Mock(return_value=mock_backlog)),
            document_processor=Mock(),
            converter=Converter(),
            task_merger=TaskMerger(category_detector, mock_logger),
            backlog_client=mock_backlog,
            storage_manager=mock_storage,
            logger=mock_logger,
        )

        # Mock fetch_data to not fail before storage
        mock_backlog.fetch_data = AsyncMock(return_value={})

        result = await wbs_service.create_wbs(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text=None,
            project_key="PROJ",
        )

        # Verify error was caught
        assert result.success is False
        assert "Storage failed" in result.error_message

    @pytest.mark.asyncio
    async def test_master_service_continues_on_partial_failure(self, mock_logger):
        """Test master service continues even if some setup fails"""
        mock_client = Mock()
        mock_client.get_issue_types = AsyncMock(return_value=[])
        mock_client.create_issue_type = AsyncMock(side_effect=Exception("API Error"))
        mock_client.get_categories = AsyncMock(return_value=[])
        mock_client.create_category = AsyncMock()
        mock_client.get_custom_fields = AsyncMock(return_value=[])
        mock_client.create_custom_field = AsyncMock()

        master_service = MasterService(mock_client, mock_logger)
        result = await master_service.setup_master_data("PROJ")

        # Verify partial success
        assert result.success is False  # Because issue type creation failed
        assert len(result.errors) > 0
        assert "issue type" in result.errors[0].lower()
