"""
Unit tests for MCP handlers
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.mcp.handlers import _task_to_summary, handle_create_wbs
from src.mcp.schemas import CreateWBSRequest
from src.models.enums import CategoryEnum
from src.models.task import Task
from src.services.wbs_service import WBSResult


class TestHandleCreateWBS:
    """Tests for handle_create_wbs function"""

    @pytest.mark.asyncio
    async def test_handle_create_wbs_success(self, mock_logger):
        """Test successful WBS creation"""
        # Create mock WBSService
        mock_wbs_service = Mock()
        mock_result = WBSResult()
        mock_result.success = True
        mock_result.registered_tasks = [
            Task(title="Task 1", category=CategoryEnum.IMPLEMENTATION, priority="高")
        ]
        mock_result.skipped_tasks = []
        mock_result.metadata_id = "meta_123"
        mock_result.master_data_created = 3
        mock_wbs_service.create_wbs = AsyncMock(return_value=mock_result)

        # Create request
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text="- Task 1 | priority: 高",
            project_key="PROJ",
        )

        # Execute handler
        response = await handle_create_wbs(request, mock_wbs_service, mock_logger)

        # Verify
        assert response.success is True
        assert len(response.registered_tasks) == 1
        assert response.registered_tasks[0].title == "Task 1"
        assert response.registered_tasks[0].category == "実装"
        assert response.metadata_id == "meta_123"
        assert response.master_data_created == 3
        assert response.total_registered == 1
        assert response.total_skipped == 0
        assert response.error_message is None

        # Verify service was called
        mock_wbs_service.create_wbs.assert_called_once_with(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text="- Task 1 | priority: 高",
            project_key="PROJ",
        )

    @pytest.mark.asyncio
    async def test_handle_create_wbs_with_skipped_tasks(self, mock_logger):
        """Test WBS creation with skipped tasks"""
        # Create mock WBSService
        mock_wbs_service = Mock()
        mock_result = WBSResult()
        mock_result.success = True
        mock_result.registered_tasks = [
            Task(title="New Task", category=CategoryEnum.TESTING)
        ]
        mock_result.skipped_tasks = [
            Task(title="Duplicate Task", category=CategoryEnum.IMPLEMENTATION)
        ]
        mock_result.metadata_id = "meta_456"
        mock_result.master_data_created = 0
        mock_wbs_service.create_wbs = AsyncMock(return_value=mock_result)

        # Create request
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1", project_key="PROJ"
        )

        # Execute handler
        response = await handle_create_wbs(request, mock_wbs_service, mock_logger)

        # Verify
        assert response.success is True
        assert len(response.registered_tasks) == 1
        assert len(response.skipped_tasks) == 1
        assert response.skipped_tasks[0].title == "Duplicate Task"
        assert response.total_registered == 1
        assert response.total_skipped == 1

    @pytest.mark.asyncio
    async def test_handle_create_wbs_failure(self, mock_logger):
        """Test WBS creation failure from service"""
        # Create mock WBSService
        mock_wbs_service = Mock()
        mock_result = WBSResult()
        mock_result.success = False
        mock_result.error_message = "Template URL not found"
        mock_result.registered_tasks = []
        mock_result.skipped_tasks = []
        mock_wbs_service.create_wbs = AsyncMock(return_value=mock_result)

        # Create request
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/INVALID", project_key="PROJ"
        )

        # Execute handler
        response = await handle_create_wbs(request, mock_wbs_service, mock_logger)

        # Verify
        assert response.success is False
        assert response.error_message == "Template URL not found"
        assert len(response.registered_tasks) == 0
        assert len(response.skipped_tasks) == 0

    @pytest.mark.asyncio
    async def test_handle_create_wbs_exception(self, mock_logger):
        """Test handler catches exceptions and returns error response"""
        # Create mock WBSService that raises exception
        mock_wbs_service = Mock()
        mock_wbs_service.create_wbs = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        # Create request
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1", project_key="PROJ"
        )

        # Execute handler
        response = await handle_create_wbs(request, mock_wbs_service, mock_logger)

        # Verify error response
        assert response.success is False
        assert "Internal error" in response.error_message
        assert "Unexpected error" in response.error_message
        assert len(response.registered_tasks) == 0
        assert len(response.skipped_tasks) == 0
        assert response.total_registered == 0
        assert response.total_skipped == 0

        # Verify logger was called
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handle_create_wbs_empty_results(self, mock_logger):
        """Test WBS creation with no tasks registered or skipped"""
        # Create mock WBSService
        mock_wbs_service = Mock()
        mock_result = WBSResult()
        mock_result.success = True
        mock_result.registered_tasks = []
        mock_result.skipped_tasks = []
        mock_result.metadata_id = "meta_789"
        mock_result.master_data_created = 5
        mock_wbs_service.create_wbs = AsyncMock(return_value=mock_result)

        # Create request
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1", project_key="PROJ"
        )

        # Execute handler
        response = await handle_create_wbs(request, mock_wbs_service, mock_logger)

        # Verify
        assert response.success is True
        assert len(response.registered_tasks) == 0
        assert len(response.skipped_tasks) == 0
        assert response.total_registered == 0
        assert response.total_skipped == 0
        assert response.metadata_id == "meta_789"
        assert response.master_data_created == 5


class TestTaskToSummary:
    """Tests for _task_to_summary helper function"""

    def test_task_to_summary_with_all_fields(self):
        """Test conversion with all task fields populated"""
        task = Task(
            title="Implementation Task",
            description="Implement feature X",
            category=CategoryEnum.IMPLEMENTATION,
            priority="高",
            assignee="Developer A",
        )

        summary = _task_to_summary(task)

        assert summary.title == "Implementation Task"
        assert summary.description == "Implement feature X"
        assert summary.category == "実装"
        assert summary.priority == "高"
        assert summary.assignee == "Developer A"

    def test_task_to_summary_with_minimal_fields(self):
        """Test conversion with minimal task fields"""
        task = Task(title="Minimal Task", category=CategoryEnum.TESTING)

        summary = _task_to_summary(task)

        assert summary.title == "Minimal Task"
        assert summary.description is None
        assert summary.category == "テスト"
        assert summary.priority is None
        assert summary.assignee is None

    def test_task_to_summary_without_category(self):
        """Test conversion when task has no category"""
        task = Task(title="Uncategorized Task")

        summary = _task_to_summary(task)

        assert summary.title == "Uncategorized Task"
        assert summary.category == "未分類"

    def test_task_to_summary_all_categories(self):
        """Test conversion for all category types"""
        categories = [
            (CategoryEnum.PREPARATION, "事前準備"),
            (CategoryEnum.REQUIREMENTS, "要件定義"),
            (CategoryEnum.BASIC_DESIGN, "基本設計"),
            (CategoryEnum.IMPLEMENTATION, "実装"),
            (CategoryEnum.TESTING, "テスト"),
            (CategoryEnum.RELEASE, "リリース"),
            (CategoryEnum.DELIVERY, "納品"),
        ]

        for cat_enum, cat_value in categories:
            task = Task(title=f"Task {cat_value}", category=cat_enum)
            summary = _task_to_summary(task)
            assert summary.category == cat_value
