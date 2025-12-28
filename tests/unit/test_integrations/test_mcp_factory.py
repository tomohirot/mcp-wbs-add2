"""
Unit tests for MCPFactory
"""

from unittest.mock import Mock, patch

import pytest

from src.integrations.mcp_factory import MCPFactory
from src.models.enums import ServiceType


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_config():
    """Create mock config"""
    config = Mock()
    config.backlog_api_key = "test-backlog-key"
    config.backlog_space_url = "https://test.backlog.com"
    config.notion_api_key = "test-notion-key"
    return config


@pytest.fixture
def mcp_factory(mock_logger, mock_config):
    """Create MCPFactory instance with mocked config"""
    with patch("src.integrations.mcp_factory.get_config", return_value=mock_config):
        return MCPFactory(mock_logger)


class TestMCPFactoryInit:
    """Tests for MCPFactory initialization"""

    def test_init_with_logger(self, mock_logger, mock_config):
        """Test initialization with logger"""
        with patch("src.integrations.mcp_factory.get_config", return_value=mock_config):
            factory = MCPFactory(mock_logger)
            assert factory.logger == mock_logger
            assert factory.config == mock_config


class TestMCPFactoryCreateClient:
    """Tests for create_client method"""

    def test_create_backlog_client(self, mcp_factory, mock_config):
        """Test creating Backlog MCP client"""
        with patch(
            "src.integrations.backlog.client.BacklogMCPClient"
        ) as MockBacklogClient:
            mock_client = Mock()
            MockBacklogClient.return_value = mock_client

            result = mcp_factory.create_client(ServiceType.BACKLOG)

            MockBacklogClient.assert_called_once_with(
                api_key=mock_config.backlog_api_key,
                space_url=mock_config.backlog_space_url,
                logger=mcp_factory.logger,
            )
            assert result == mock_client

    def test_create_notion_client(self, mcp_factory, mock_config):
        """Test creating Notion MCP client"""
        with patch(
            "src.integrations.notion.client.NotionMCPClient"
        ) as MockNotionClient:
            mock_client = Mock()
            MockNotionClient.return_value = mock_client

            result = mcp_factory.create_client(ServiceType.NOTION)

            MockNotionClient.assert_called_once_with(
                api_key=mock_config.notion_api_key, logger=mcp_factory.logger
            )
            assert result == mock_client

    def test_create_client_logs_backlog(self, mcp_factory, mock_logger):
        """Test that creating Backlog client logs message"""
        with patch("src.integrations.backlog.client.BacklogMCPClient"):
            mcp_factory.create_client(ServiceType.BACKLOG)
            mock_logger.info.assert_called_with("Creating Backlog MCP client")

    def test_create_client_logs_notion(self, mcp_factory, mock_logger):
        """Test that creating Notion client logs message"""
        with patch("src.integrations.notion.client.NotionMCPClient"):
            mcp_factory.create_client(ServiceType.NOTION)
            mock_logger.info.assert_called_with("Creating Notion MCP client")

    def test_create_client_invalid_service_type(self, mcp_factory):
        """Test creating client with invalid service type raises ValueError"""
        with pytest.raises(ValueError, match="サポートされていないサービスタイプです"):
            # Use a mock object that's not a valid ServiceType
            mcp_factory.create_client("INVALID")
