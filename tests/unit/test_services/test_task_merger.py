"""
Unit tests for TaskMerger
"""

from unittest.mock import Mock

import pytest

from src.models.enums import CategoryEnum
from src.models.task import Task
from src.services.category_detector import CategoryDetector
from src.services.task_merger import TaskMerger


@pytest.fixture
def mock_category_detector():
    """Mock CategoryDetector"""
    detector = Mock(spec=CategoryDetector)
    detector.detect_category = Mock(return_value=CategoryEnum.IMPLEMENTATION)
    return detector


@pytest.fixture
def task_merger(mock_logger, mock_category_detector):
    """Create TaskMerger instance with mocks"""
    return TaskMerger(mock_category_detector, mock_logger)


class TestTaskMerger:
    """Tests for TaskMerger class"""

    def test_merge_tasks_empty_lists(self, task_merger):
        """Test merging empty task lists"""
        result = task_merger.merge_tasks([], [])
        assert len(result) == 0

    def test_merge_tasks_template_only(self, task_merger):
        """Test merging with template tasks only"""
        template_tasks = [
            Task(title="Template1", category=CategoryEnum.REQUIREMENTS),
            Task(title="Template2", category=CategoryEnum.IMPLEMENTATION),
        ]
        result = task_merger.merge_tasks(template_tasks, [])
        assert len(result) == 2
        assert result[0].title == "Template1"

    def test_merge_tasks_new_only(self, task_merger, mock_category_detector):
        """Test merging with new tasks only"""
        new_tasks = [Task(title="New1"), Task(title="New2")]
        mock_category_detector.detect_category.return_value = CategoryEnum.TESTING

        result = task_merger.merge_tasks([], new_tasks)
        assert len(result) == 2

    def test_merge_tasks_preserves_category_order(self, task_merger):
        """Test tasks are sorted by category order"""
        tasks = [
            Task(title="Task1", category=CategoryEnum.TESTING),
            Task(title="Task2", category=CategoryEnum.REQUIREMENTS),
            Task(title="Task3", category=CategoryEnum.IMPLEMENTATION),
        ]
        result = task_merger.merge_tasks(tasks, [])
        assert result[0].category == CategoryEnum.REQUIREMENTS
        assert result[1].category == CategoryEnum.IMPLEMENTATION
        assert result[2].category == CategoryEnum.TESTING

    def test_merge_tasks_template_before_new(self, task_merger, mock_category_detector):
        """Test template tasks come before new tasks in same category"""
        template = [Task(title="Template", category=CategoryEnum.IMPLEMENTATION)]
        new = [Task(title="New")]
        mock_category_detector.detect_category.return_value = (
            CategoryEnum.IMPLEMENTATION
        )

        result = task_merger.merge_tasks(template, new)
        assert result[0].title == "Template"
        assert result[1].title == "New"

    def test_get_category_order_index(self, task_merger):
        """Test category order index retrieval"""
        assert task_merger.get_category_order_index(CategoryEnum.PREPARATION) == 0
        assert task_merger.get_category_order_index(CategoryEnum.REQUIREMENTS) == 1
        assert task_merger.get_category_order_index(CategoryEnum.DELIVERY) == 6

    def test_sort_tasks_by_category(self, task_merger):
        """Test sorting tasks by category"""
        tasks = [
            Task(title="T1", category=CategoryEnum.DELIVERY),
            Task(title="T2", category=CategoryEnum.PREPARATION),
        ]
        result = task_merger.sort_tasks_by_category(tasks)
        assert result[0].category == CategoryEnum.PREPARATION
        assert result[1].category == CategoryEnum.DELIVERY
