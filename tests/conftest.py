"""
Pytest configuration and shared fixtures
"""

import os
import sys
from unittest.mock import Mock

import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


@pytest.fixture
def mock_logger():
    """Mock Logger fixture"""
    logger = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "title": "テストタスク",
        "description": "テストの説明",
        "category": "要件定義",
        "priority": "高",
        "assignee": "担当者A",
    }


@pytest.fixture
def sample_tasks_text():
    """Sample tasks text in Markdown format"""
    return """
- 要件定義タスク1 | priority: 高 | category: 要件定義
- 実装タスク1 | priority: 中 | category: 実装
- テストタスク1 | priority: 低
"""


@pytest.fixture
def sample_backlog_url():
    """Sample Backlog URL"""
    return "https://example.backlog.com/view/PROJ-123"


@pytest.fixture
def sample_notion_url():
    """Sample Notion URL"""
    return "https://www.notion.so/workspace/Page-Title-abc123def456"


@pytest.fixture
def mock_config():
    """Mock Config fixture"""
    config = Mock()
    config.gcp_project_id = "test-project"
    config.gcs_bucket_name = "test-bucket"
    config.backlog_api_key = "test-backlog-key"
    config.backlog_space_url = "https://test.backlog.com"
    config.notion_api_key = "test-notion-key"
    config.document_ai_processor_id = "test-processor"
    return config
