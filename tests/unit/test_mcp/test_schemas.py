"""
Unit tests for MCP schemas
"""

import pytest
from pydantic import ValidationError

from src.mcp.schemas import CreateWBSRequest, CreateWBSResponse, TaskSummary


class TestCreateWBSRequest:
    """Tests for CreateWBSRequest schema"""

    def test_valid_request_minimal(self):
        """Test valid request with minimal fields"""
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1",
            project_key="PROJ",
        )
        assert request.template_url == "https://test.backlog.com/view/PROJ-1"
        assert request.project_key == "PROJ"
        assert request.new_tasks_text is None

    def test_valid_request_with_new_tasks(self):
        """Test valid request with new tasks"""
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text="- Task 1 | priority: 高\n- Task 2",
            project_key="PROJ",
        )
        assert request.new_tasks_text == "- Task 1 | priority: 高\n- Task 2"

    def test_missing_template_url_raises_error(self):
        """Test that missing template_url raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            CreateWBSRequest(project_key="PROJ")
        assert "template_url" in str(exc_info.value)

    def test_missing_project_key_raises_error(self):
        """Test that missing project_key raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            CreateWBSRequest(template_url="https://test.backlog.com/view/PROJ-1")
        assert "project_key" in str(exc_info.value)

    def test_empty_template_url_raises_error(self):
        """Test that empty template_url raises ValidationError"""
        with pytest.raises(ValidationError):
            CreateWBSRequest(template_url="", project_key="PROJ")

    def test_empty_project_key_raises_error(self):
        """Test that empty project_key raises ValidationError"""
        with pytest.raises(ValidationError):
            CreateWBSRequest(
                template_url="https://test.backlog.com/view/PROJ-1", project_key=""
            )

    def test_project_key_max_length(self):
        """Test project_key max length validation"""
        # 50 characters should be ok
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1",
            project_key="A" * 50,
        )
        assert len(request.project_key) == 50

        # 51 characters should fail
        with pytest.raises(ValidationError):
            CreateWBSRequest(
                template_url="https://test.backlog.com/view/PROJ-1",
                project_key="A" * 51,
            )

    def test_request_json_serialization(self):
        """Test JSON serialization"""
        request = CreateWBSRequest(
            template_url="https://test.backlog.com/view/PROJ-1",
            new_tasks_text="- Task 1",
            project_key="PROJ",
        )
        json_data = request.model_dump()
        assert json_data["template_url"] == "https://test.backlog.com/view/PROJ-1"
        assert json_data["new_tasks_text"] == "- Task 1"
        assert json_data["project_key"] == "PROJ"


class TestTaskSummary:
    """Tests for TaskSummary schema"""

    def test_valid_task_summary_minimal(self):
        """Test valid task summary with minimal fields"""
        task = TaskSummary(title="Test Task", category="実装")
        assert task.title == "Test Task"
        assert task.category == "実装"
        assert task.description is None
        assert task.priority is None
        assert task.assignee is None

    def test_valid_task_summary_full(self):
        """Test valid task summary with all fields"""
        task = TaskSummary(
            title="Test Task",
            description="Task description",
            category="実装",
            priority="高",
            assignee="担当者A",
        )
        assert task.title == "Test Task"
        assert task.description == "Task description"
        assert task.category == "実装"
        assert task.priority == "高"
        assert task.assignee == "担当者A"

    def test_missing_title_raises_error(self):
        """Test that missing title raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            TaskSummary(category="実装")
        assert "title" in str(exc_info.value)

    def test_missing_category_raises_error(self):
        """Test that missing category raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            TaskSummary(title="Test Task")
        assert "category" in str(exc_info.value)


class TestCreateWBSResponse:
    """Tests for CreateWBSResponse schema"""

    def test_valid_response_success(self):
        """Test valid success response"""
        response = CreateWBSResponse(
            success=True,
            registered_tasks=[
                TaskSummary(title="Task 1", category="実装", priority="高")
            ],
            skipped_tasks=[],
            metadata_id="meta_123",
            master_data_created=3,
            total_registered=1,
            total_skipped=0,
        )
        assert response.success is True
        assert len(response.registered_tasks) == 1
        assert response.registered_tasks[0].title == "Task 1"
        assert response.metadata_id == "meta_123"
        assert response.master_data_created == 3
        assert response.error_message is None

    def test_valid_response_failure(self):
        """Test valid failure response"""
        response = CreateWBSResponse(
            success=False,
            error_message="Something went wrong",
            registered_tasks=[],
            skipped_tasks=[],
        )
        assert response.success is False
        assert response.error_message == "Something went wrong"
        assert len(response.registered_tasks) == 0
        assert len(response.skipped_tasks) == 0

    def test_default_values(self):
        """Test default values are set correctly"""
        response = CreateWBSResponse(success=True)
        assert response.registered_tasks == []
        assert response.skipped_tasks == []
        assert response.error_message is None
        assert response.metadata_id is None
        assert response.master_data_created == 0
        assert response.total_registered == 0
        assert response.total_skipped == 0

    def test_missing_success_raises_error(self):
        """Test that missing success field raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            CreateWBSResponse()
        assert "success" in str(exc_info.value)

    def test_response_json_serialization(self):
        """Test JSON serialization"""
        response = CreateWBSResponse(
            success=True,
            registered_tasks=[
                TaskSummary(title="Task 1", category="実装"),
                TaskSummary(title="Task 2", category="テスト"),
            ],
            skipped_tasks=[TaskSummary(title="Duplicate", category="実装")],
            metadata_id="meta_abc",
            master_data_created=5,
            total_registered=2,
            total_skipped=1,
        )
        json_data = response.model_dump()
        assert json_data["success"] is True
        assert len(json_data["registered_tasks"]) == 2
        assert len(json_data["skipped_tasks"]) == 1
        assert json_data["metadata_id"] == "meta_abc"
        assert json_data["master_data_created"] == 5

    def test_response_with_skipped_tasks(self):
        """Test response with skipped tasks"""
        response = CreateWBSResponse(
            success=True,
            registered_tasks=[],
            skipped_tasks=[
                TaskSummary(title="Duplicate 1", category="実装"),
                TaskSummary(title="Duplicate 2", category="テスト"),
            ],
            total_registered=0,
            total_skipped=2,
        )
        assert response.success is True
        assert len(response.registered_tasks) == 0
        assert len(response.skipped_tasks) == 2
        assert response.total_skipped == 2
