"""
Unit tests for MCP server
"""

from unittest.mock import Mock, patch

import pytest

from src.mcp.handlers import handle_create_wbs
from src.mcp.schemas import CreateWBSRequest
from src.mcp.server import create_mcp_server, get_server_metadata


class TestCreateMCPServer:
    """Tests for create_mcp_server function"""

    @pytest.mark.asyncio
    async def test_create_mcp_server_returns_config(self, mock_logger):
        """Test that create_mcp_server returns server configuration"""
        with patch("src.mcp.server.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.gcp_project_id = "test-project"
            mock_get_config.return_value = mock_config

            server_config = await create_mcp_server(mock_logger)

            assert isinstance(server_config, dict)
            assert "name" in server_config
            assert "version" in server_config
            assert "handlers" in server_config
            assert "config" in server_config

    @pytest.mark.asyncio
    async def test_create_mcp_server_config_structure(self, mock_logger):
        """Test server configuration structure"""
        with patch("src.mcp.server.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.gcp_project_id = "my-project"
            mock_get_config.return_value = mock_config

            server_config = await create_mcp_server(mock_logger)

            # Verify top-level structure
            assert server_config["name"] == "wbs-creation-server"
            assert server_config["version"] == "1.0.0"

            # Verify handlers
            assert "create_wbs" in server_config["handlers"]
            handler_info = server_config["handlers"]["create_wbs"]
            assert handler_info["function"] == handle_create_wbs
            assert handler_info["request_schema"] == CreateWBSRequest

            # Verify config
            assert server_config["config"]["gcp_project_id"] == "my-project"
            assert server_config["config"]["environment"] == "production"

    @pytest.mark.asyncio
    async def test_create_mcp_server_logs_creation(self, mock_logger):
        """Test that server creation is logged"""
        with patch("src.mcp.server.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.gcp_project_id = "test-project"
            mock_get_config.return_value = mock_config

            await create_mcp_server(mock_logger)

            # Verify logger was called
            assert mock_logger.info.call_count >= 2
            mock_logger.info.assert_any_call("Creating MCP server")
            mock_logger.info.assert_any_call("MCP server created successfully")


class TestGetServerMetadata:
    """Tests for get_server_metadata function"""

    def test_get_server_metadata_returns_dict(self):
        """Test that get_server_metadata returns metadata dict"""
        metadata = get_server_metadata()

        assert isinstance(metadata, dict)
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata
        assert "capabilities" in metadata
        assert "supported_services" in metadata

    def test_get_server_metadata_structure(self):
        """Test server metadata structure"""
        metadata = get_server_metadata()

        assert metadata["name"] == "WBS Creation MCP Server"
        assert metadata["version"] == "1.0.0"
        assert "WBS creation" in metadata["description"]
        assert "create_wbs" in metadata["capabilities"]
        assert "Backlog" in metadata["supported_services"]
        assert "Notion" in metadata["supported_services"]

    def test_get_server_metadata_capabilities_list(self):
        """Test capabilities is a list"""
        metadata = get_server_metadata()

        assert isinstance(metadata["capabilities"], list)
        assert len(metadata["capabilities"]) > 0

    def test_get_server_metadata_supported_services_list(self):
        """Test supported_services is a list"""
        metadata = get_server_metadata()

        assert isinstance(metadata["supported_services"], list)
        assert len(metadata["supported_services"]) == 2

    def test_get_server_metadata_is_consistent(self):
        """Test that metadata is consistent across calls"""
        metadata1 = get_server_metadata()
        metadata2 = get_server_metadata()

        assert metadata1 == metadata2
