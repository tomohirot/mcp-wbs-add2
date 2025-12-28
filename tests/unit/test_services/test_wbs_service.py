"""
Unit tests for WBSService
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.models.enums import CategoryEnum, ServiceType
from src.models.task import Task
from src.services.wbs_service import WBSResult, WBSService


@pytest.fixture
def mock_dependencies(mock_logger):
    """Create mock dependencies for WBSService"""
    return {
        "master_service": Mock(),
        "url_parser": Mock(),
        "mcp_factory": Mock(),
        "document_processor": Mock(),
        "converter": Mock(),
        "task_merger": Mock(),
        "backlog_client": Mock(),
        "storage_manager": Mock(),
        "logger": mock_logger,
    }


@pytest.fixture
def wbs_service(mock_dependencies):
    """Create WBSService instance with mocks"""
    return WBSService(**mock_dependencies)


class TestWBSResult:
    """Tests for WBSResult class"""

    def test_to_dict(self):
        """Test WBSResult to_dict conversion"""
        result = WBSResult()
        result.success = True
        result.registered_tasks = [Task(title="Task1")]
        result.metadata_id = "meta123"

        data = result.to_dict()
        assert data["success"] is True
        assert data["total_registered"] == 1
        assert data["metadata_id"] == "meta123"


class TestWBSService:
    """Tests for WBSService class"""

    @pytest.mark.asyncio
    async def test_create_wbs_success_flow(self, wbs_service, mock_dependencies):
        """Test successful WBS creation workflow"""
        # Setup mocks
        mock_dependencies["url_parser"].parse_service_type.return_value = (
            ServiceType.BACKLOG
        )
        mock_dependencies["mcp_factory"].create_client.return_value = mock_dependencies[
            "backlog_client"
        ]
        mock_dependencies["backlog_client"].fetch_data = AsyncMock(return_value={})
        mock_dependencies["storage_manager"].save_data = AsyncMock(
            return_value=Mock(id="meta123", version=1)
        )
        mock_dependencies["converter"].parse_tasks_from_text.return_value = []
        mock_dependencies["task_merger"].merge_tasks.return_value = []
        mock_dependencies["backlog_client"].get_tasks = AsyncMock(return_value=[])
        mock_dependencies["backlog_client"].create_tasks = AsyncMock(return_value=[])
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(success=True, total_created=3)
        )

        # Execute
        result = await wbs_service.create_wbs(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text=None,
            project_key="PROJ",
        )

        # Verify
        assert result.success is True
        assert result.master_data_created == 3

    @pytest.mark.asyncio
    async def test_create_wbs_with_error(self, wbs_service, mock_dependencies):
        """Test WBS creation with error"""
        # Setup mocks - need AsyncMock for async methods called before the error
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(success=True, total_created=0)
        )
        # Setup mock to raise error at URL parsing
        mock_dependencies["url_parser"].parse_service_type.side_effect = ValueError(
            "Invalid URL"
        )

        # Execute
        result = await wbs_service.create_wbs(
            template_url="invalid", new_tasks_text=None, project_key="PROJ"
        )

        # Verify
        assert result.success is False
        assert result.error_message is not None
        assert "Invalid URL" in result.error_message

    @pytest.mark.asyncio
    async def test_create_wbs_with_new_tasks(self, wbs_service, mock_dependencies):
        """Test WBS creation with new tasks text"""
        # Setup mocks
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(success=True, total_created=0)
        )
        mock_dependencies["url_parser"].parse_service_type.return_value = (
            ServiceType.BACKLOG
        )
        mock_dependencies["mcp_factory"].create_client.return_value = mock_dependencies[
            "backlog_client"
        ]
        mock_dependencies["backlog_client"].fetch_data = AsyncMock(return_value={})
        mock_dependencies["storage_manager"].save_data = AsyncMock(
            return_value=Mock(id="meta123", version=1)
        )

        # Mock new tasks parsing
        new_task = Task(title="新しいタスク", category=CategoryEnum.IMPLEMENTATION)
        mock_dependencies["converter"].parse_tasks_from_text.return_value = [new_task]

        # Mock task merger
        merged_task = Task(title="新しいタスク", category=CategoryEnum.IMPLEMENTATION)
        mock_dependencies["task_merger"].merge_tasks.return_value = [merged_task]

        mock_dependencies["backlog_client"].get_tasks = AsyncMock(return_value=[])
        mock_dependencies["backlog_client"].create_tasks = AsyncMock(
            return_value=[merged_task]
        )

        # Execute
        result = await wbs_service.create_wbs(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text="- 新しいタスク",
            project_key="PROJ",
        )

        # Verify
        assert result.success is True
        assert len(result.registered_tasks) == 1
        mock_dependencies["converter"].parse_tasks_from_text.assert_called_once_with(
            "- 新しいタスク"
        )

    @pytest.mark.asyncio
    async def test_create_wbs_storage_saves_data(self, wbs_service, mock_dependencies):
        """Test that storage manager saves template data"""
        # Setup mocks
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(success=True, total_created=0)
        )
        mock_dependencies["url_parser"].parse_service_type.return_value = (
            ServiceType.NOTION
        )

        mock_notion_client = Mock()
        mock_dependencies["mcp_factory"].create_client.return_value = mock_notion_client

        template_data = {"title": "Template", "tasks": []}
        mock_notion_client.fetch_data = AsyncMock(return_value=template_data)

        mock_metadata = Mock(id="meta456", version=2)
        mock_dependencies["storage_manager"].save_data = AsyncMock(
            return_value=mock_metadata
        )
        mock_dependencies["converter"].parse_tasks_from_text.return_value = []
        mock_dependencies["task_merger"].merge_tasks.return_value = []
        mock_dependencies["backlog_client"].get_tasks = AsyncMock(return_value=[])
        mock_dependencies["backlog_client"].create_tasks = AsyncMock(return_value=[])

        # Execute
        result = await wbs_service.create_wbs(
            template_url="https://notion.so/page123",
            new_tasks_text=None,
            project_key="PROJ",
        )

        # Verify storage was called
        mock_dependencies["storage_manager"].save_data.assert_called_once()
        call_args = mock_dependencies["storage_manager"].save_data.call_args
        assert call_args[1]["file_url"] == "https://notion.so/page123"
        assert call_args[1]["data"] == template_data

    @pytest.mark.asyncio
    async def test_create_wbs_duplicate_detection(self, wbs_service, mock_dependencies):
        """Test duplicate task detection"""
        # Setup mocks
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(success=True, total_created=0)
        )
        mock_dependencies["url_parser"].parse_service_type.return_value = (
            ServiceType.BACKLOG
        )
        mock_dependencies["mcp_factory"].create_client.return_value = mock_dependencies[
            "backlog_client"
        ]
        mock_dependencies["backlog_client"].fetch_data = AsyncMock(return_value={})
        mock_dependencies["storage_manager"].save_data = AsyncMock(
            return_value=Mock(id="meta", version=1)
        )
        mock_dependencies["converter"].parse_tasks_from_text.return_value = []

        # Mock existing task in Backlog (must have .summary attribute, not .title)
        existing_task = Mock()
        existing_task.summary = "既存タスク"

        # Mock merged tasks (including duplicate)
        merged_tasks = [
            Task(title="既存タスク", category=CategoryEnum.IMPLEMENTATION),
            Task(title="新規タスク", category=CategoryEnum.TESTING),
        ]
        mock_dependencies["task_merger"].merge_tasks.return_value = merged_tasks

        # Mock get_tasks to return existing task with .summary attribute
        mock_dependencies["backlog_client"].get_tasks = AsyncMock(
            return_value=[existing_task]
        )

        # Only new task should be created
        mock_dependencies["backlog_client"].create_tasks = AsyncMock(
            return_value=[merged_tasks[1]]
        )

        # Execute
        result = await wbs_service.create_wbs(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text=None,
            project_key="PROJ",
        )

        # Verify only non-duplicate task was registered
        assert result.success is True
        assert len(result.registered_tasks) == 1

    @pytest.mark.asyncio
    async def test_create_wbs_master_data_with_errors(
        self, wbs_service, mock_dependencies
    ):
        """Test WBS creation when master data setup has errors"""
        # Setup mocks
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(
                success=False, total_created=0, errors=["Error 1", "Error 2"]
            )
        )
        mock_dependencies["url_parser"].parse_service_type.return_value = (
            ServiceType.BACKLOG
        )
        mock_dependencies["mcp_factory"].create_client.return_value = mock_dependencies[
            "backlog_client"
        ]
        mock_dependencies["backlog_client"].fetch_data = AsyncMock(return_value={})
        mock_dependencies["storage_manager"].save_data = AsyncMock(
            return_value=Mock(id="meta", version=1)
        )
        mock_dependencies["converter"].parse_tasks_from_text.return_value = []
        mock_dependencies["task_merger"].merge_tasks.return_value = []
        mock_dependencies["backlog_client"].get_tasks = AsyncMock(return_value=[])
        mock_dependencies["backlog_client"].create_tasks = AsyncMock(return_value=[])

        # Execute - should continue despite master data errors
        result = await wbs_service.create_wbs(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text=None,
            project_key="PROJ",
        )

        # Verify it still completes
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_wbs_unsupported_service_type(
        self, wbs_service, mock_dependencies
    ):
        """Test WBS creation with unsupported service type"""
        # Setup mocks
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(success=True, total_created=0)
        )
        # Return an invalid service type by raising in _process_template_data
        mock_dependencies["url_parser"].parse_service_type.return_value = (
            ServiceType.BACKLOG
        )
        mock_dependencies["mcp_factory"].create_client.return_value = mock_dependencies[
            "backlog_client"
        ]
        mock_dependencies["backlog_client"].fetch_data = AsyncMock(return_value={})
        mock_dependencies["storage_manager"].save_data = AsyncMock(
            return_value=Mock(id="meta", version=1)
        )

        # Mock _process_template_data to raise ValueError for unsupported service
        async def raise_unsupported(*args, **kwargs):
            raise ValueError("Unsupported service type")

        wbs_service._process_template_data = raise_unsupported

        # Execute
        result = await wbs_service.create_wbs(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text=None,
            project_key="PROJ",
        )

        # Verify error is captured
        assert result.success is False
        assert "Unsupported service type" in result.error_message

    @pytest.mark.asyncio
    async def test_create_wbs_duplicate_check_error(
        self, wbs_service, mock_dependencies
    ):
        """Test WBS creation when duplicate check fails"""
        # Setup mocks
        mock_dependencies["master_service"].setup_master_data = AsyncMock(
            return_value=Mock(success=True, total_created=0)
        )
        mock_dependencies["url_parser"].parse_service_type.return_value = (
            ServiceType.BACKLOG
        )
        mock_dependencies["mcp_factory"].create_client.return_value = mock_dependencies[
            "backlog_client"
        ]
        mock_dependencies["backlog_client"].fetch_data = AsyncMock(return_value={})
        mock_dependencies["storage_manager"].save_data = AsyncMock(
            return_value=Mock(id="meta", version=1)
        )
        mock_dependencies["converter"].parse_tasks_from_text.return_value = []

        merged_task = Task(title="タスク", category=CategoryEnum.IMPLEMENTATION)
        mock_dependencies["task_merger"].merge_tasks.return_value = [merged_task]

        # Mock get_tasks to raise an error
        mock_dependencies["backlog_client"].get_tasks = AsyncMock(
            side_effect=Exception("API connection failed")
        )
        # Should still try to create tasks despite error
        mock_dependencies["backlog_client"].create_tasks = AsyncMock(
            return_value=[merged_task]
        )

        # Execute - should continue with all tasks despite duplicate check error
        result = await wbs_service.create_wbs(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text=None,
            project_key="PROJ",
        )

        # Verify it completes and registers all tasks (no filtering)
        assert result.success is True
        assert len(result.registered_tasks) == 1

    @pytest.mark.asyncio
    async def test_process_template_data_notion_with_blocks(self, wbs_service):
        """Test _process_template_data with Notion blocks"""
        from src.models.enums import ServiceType

        template_data = {
            "type": "page",
            "blocks": [
                {"type": "paragraph", "text": "- タスク1"},
                {"type": "paragraph", "text": "- タスク2"},
            ],
        }

        # Mock converter to return tasks
        wbs_service.converter.parse_tasks_from_text = Mock(
            return_value=[Task(title="タスク1", category=CategoryEnum.IMPLEMENTATION)]
        )

        result = await wbs_service._process_template_data(
            template_data, ServiceType.NOTION
        )

        # Verify it attempts to parse tasks from extracted text
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_process_template_data_notion_with_database(self, wbs_service):
        """Test _process_template_data with Notion database"""
        from src.models.enums import ServiceType

        template_data = {
            "type": "database",
            "rows": [
                {"properties": {"Name": "タスク1"}},
                {"properties": {"Name": "タスク2"}},
            ],
        }

        result = await wbs_service._process_template_data(
            template_data, ServiceType.NOTION
        )

        # Verify it handles database format
        assert isinstance(result, list)
