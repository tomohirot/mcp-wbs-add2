"""
Unit tests for NotionMCPClient
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.integrations.notion.client import NotionMCPClient
from src.integrations.notion.models import NotionBlock, NotionDatabase, NotionPage


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
def notion_client(mock_logger):
    """Create NotionMCPClient instance"""
    return NotionMCPClient(api_key="test-api-key", logger=mock_logger)


class TestNotionMCPClientInit:
    """Tests for NotionMCPClient initialization"""

    def test_init(self, mock_logger):
        """Test NotionMCPClient initialization"""
        client = NotionMCPClient(
            api_key="my-secret-key", logger=mock_logger, timeout=60
        )
        assert client.api_key == "my-secret-key"
        assert client.logger == mock_logger
        assert client.timeout == 60
        assert client.api_base_url == "https://api.notion.com/v1"
        assert client.max_retries == 3
        assert client.retry_delay == 1.0

    def test_init_default_timeout(self, mock_logger):
        """Test initialization with default timeout"""
        client = NotionMCPClient(api_key="key", logger=mock_logger)
        assert client.timeout == 30


class TestExtractIdFromUrl:
    """Tests for _extract_id_from_url method"""

    def test_extract_id_from_url_with_hyphens(self, notion_client):
        """Test extracting UUID format ID from URL"""
        url = "https://www.notion.so/workspace/Page-Title-12345678-1234-1234-1234-123456789abc"
        result = notion_client._extract_id_from_url(url)
        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_extract_id_from_url_without_hyphens(self, notion_client):
        """Test extracting 32-char ID and converting to UUID format"""
        url = "https://www.notion.so/workspace/Page-Title-12345678123412341234123456789abc"
        result = notion_client._extract_id_from_url(url)
        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_extract_id_from_short_url(self, notion_client):
        """Test extracting ID from short Notion URL"""
        url = "https://notion.so/abcdef12345678901234567890123456"
        result = notion_client._extract_id_from_url(url)
        assert result == "abcdef12-3456-7890-1234-567890123456"

    def test_extract_id_from_url_case_insensitive(self, notion_client):
        """Test ID extraction is case insensitive"""
        url = "https://www.notion.so/ABCDEF12-3456-7890-1234-567890123456"
        result = notion_client._extract_id_from_url(url)
        assert result == "abcdef12-3456-7890-1234-567890123456"

    def test_extract_id_from_url_invalid(self, notion_client):
        """Test extraction from invalid URL returns None"""
        url = "https://invalid-url.com/not-notion"
        result = notion_client._extract_id_from_url(url)
        assert result is None

    def test_extract_id_from_url_no_id(self, notion_client):
        """Test extraction from URL without ID returns None"""
        url = "https://www.notion.so/workspace/Page-Title"
        result = notion_client._extract_id_from_url(url)
        assert result is None


class TestCallMCP:
    """Tests for _call_mcp method"""

    @pytest.mark.asyncio
    async def test_call_mcp_success(self, notion_client, mock_logger):
        """Test successful MCP call"""
        result = await notion_client._call_mcp("GET", "/pages/test-id")
        assert isinstance(result, dict)
        # Verify logging
        assert mock_logger.debug.called
        assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_call_mcp_with_params(self, notion_client):
        """Test MCP call with query parameters"""
        result = await notion_client._call_mcp(
            "GET", "/databases/test-id/query", params={"filter": "test"}
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_call_mcp_with_data(self, notion_client):
        """Test MCP call with request body"""
        result = await notion_client._call_mcp(
            "POST", "/pages", data={"properties": {"title": "Test"}}
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_call_mcp_retry_on_failure(self, notion_client, mock_logger):
        """Test retry logic on transient failures"""
        # Mock asyncio.sleep to speed up test
        with patch("asyncio.sleep", new_callable=AsyncMock):
            # Since _call_mcp currently just returns {}, we can't easily test retry
            # This is a placeholder test for when actual implementation is added
            result = await notion_client._call_mcp("GET", "/pages/test-id")
            assert isinstance(result, dict)


class TestFetchData:
    """Tests for fetch_data method"""

    @pytest.mark.asyncio
    async def test_fetch_data_as_page(self, notion_client):
        """Test fetching data as a page"""
        with patch.object(
            notion_client, "_fetch_page_with_blocks", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = {
                "type": "page",
                "data": {"id": "test-id"},
                "blocks": [],
            }

            url = "https://notion.so/12345678123412341234123456789abc"
            result = await notion_client.fetch_data(url)

            assert result["type"] == "page"
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_data_as_database(self, notion_client):
        """Test fetching data as a database when page fetch fails"""
        with patch.object(
            notion_client, "_fetch_page_with_blocks", new_callable=AsyncMock
        ) as mock_page:
            with patch.object(
                notion_client, "_fetch_database_with_rows", new_callable=AsyncMock
            ) as mock_db:
                mock_page.side_effect = Exception("Not a page")
                mock_db.return_value = {
                    "type": "database",
                    "data": {"id": "test-id"},
                    "rows": [],
                }

                url = "https://notion.so/12345678123412341234123456789abc"
                result = await notion_client.fetch_data(url)

                assert result["type"] == "database"
                mock_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_data_invalid_url(self, notion_client):
        """Test fetch_data with invalid URL raises ValueError"""
        with pytest.raises(ValueError, match="Invalid Notion URL"):
            await notion_client.fetch_data("https://invalid-url.com")

    @pytest.mark.asyncio
    async def test_fetch_data_both_methods_fail(self, notion_client):
        """Test fetch_data when both page and database fetch fail"""
        with patch.object(
            notion_client, "_fetch_page_with_blocks", new_callable=AsyncMock
        ) as mock_page:
            with patch.object(
                notion_client, "_fetch_database_with_rows", new_callable=AsyncMock
            ) as mock_db:
                mock_page.side_effect = Exception("Page error")
                mock_db.side_effect = Exception("Database error")

                url = "https://notion.so/12345678123412341234123456789abc"
                with pytest.raises(
                    ValueError, match="Could not fetch data from URL as page or database"
                ):
                    await notion_client.fetch_data(url)


class TestFetchPageWithBlocks:
    """Tests for _fetch_page_with_blocks method"""

    @pytest.mark.asyncio
    async def test_fetch_page_with_blocks(self, notion_client):
        """Test fetching page with blocks"""
        with patch.object(
            notion_client, "_call_mcp", new_callable=AsyncMock
        ) as mock_call:
            mock_call.side_effect = [
                {"id": "page-id", "properties": {}},  # Page response
                {"results": [{"type": "paragraph"}]},  # Blocks response
            ]

            result = await notion_client._fetch_page_with_blocks("test-page-id")

            assert result["type"] == "page"
            assert "data" in result
            assert "blocks" in result
            assert len(result["blocks"]) == 1
            assert mock_call.call_count == 2


class TestFetchDatabaseWithRows:
    """Tests for _fetch_database_with_rows method"""

    @pytest.mark.asyncio
    async def test_fetch_database_with_rows(self, notion_client):
        """Test fetching database with rows"""
        with patch.object(
            notion_client, "_call_mcp", new_callable=AsyncMock
        ) as mock_call:
            mock_call.side_effect = [
                {"id": "db-id", "title": []},  # Database response
                {
                    "results": [{"id": "row1"}, {"id": "row2"}]
                },  # Query response
            ]

            result = await notion_client._fetch_database_with_rows("test-db-id")

            assert result["type"] == "database"
            assert "data" in result
            assert "rows" in result
            assert len(result["rows"]) == 2
            assert mock_call.call_count == 2


class TestGetPage:
    """Tests for get_page method"""

    @pytest.mark.asyncio
    async def test_get_page(self, notion_client):
        """Test getting a page"""
        with patch.object(notion_client, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {}  # Empty response triggers placeholder
            page = await notion_client.get_page("test-page-id")

            assert isinstance(page, NotionPage)
            assert page.id == "test-page-id"


class TestGetBlocks:
    """Tests for get_blocks method"""

    @pytest.mark.asyncio
    async def test_get_blocks(self, notion_client):
        """Test getting blocks"""
        with patch.object(notion_client, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"results": []}  # Empty results
            blocks = await notion_client.get_blocks("test-block-id")

            assert isinstance(blocks, list)


class TestGetDatabase:
    """Tests for get_database method"""

    @pytest.mark.asyncio
    async def test_get_database(self, notion_client):
        """Test getting a database"""
        with patch.object(notion_client, "_call_mcp", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {}  # Empty response triggers placeholder
            database = await notion_client.get_database("test-db-id")

            assert isinstance(database, NotionDatabase)
            assert database.id == "test-db-id"


class TestQueryDatabase:
    """Tests for query_database method"""

    @pytest.mark.asyncio
    async def test_query_database_basic(self, notion_client):
        """Test basic database query"""
        with patch.object(
            notion_client, "_call_mcp", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = {"results": []}  # Empty results list

            pages = await notion_client.query_database("test-db-id")

            assert isinstance(pages, list)
            assert len(pages) == 0
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_database_with_filter(self, notion_client):
        """Test database query with filter"""
        with patch.object(
            notion_client, "_call_mcp", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = {"results": []}  # Empty results list

            filter_conditions = {"property": "Status", "select": {"equals": "Active"}}
            await notion_client.query_database("test-db-id", filter_conditions)

            # Verify filter was passed to MCP call
            call_args = mock_call.call_args
            assert "data" in call_args.kwargs
            assert "filter" in call_args.kwargs["data"]

    @pytest.mark.asyncio
    async def test_query_database_with_sorts(self, notion_client):
        """Test database query with sorts"""
        with patch.object(
            notion_client, "_call_mcp", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = {"results": []}  # Empty results list

            sorts = [{"property": "Name", "direction": "ascending"}]
            await notion_client.query_database("test-db-id", sorts=sorts)

            # Verify sorts was passed to MCP call
            call_args = mock_call.call_args
            assert "data" in call_args.kwargs
            assert "sorts" in call_args.kwargs["data"]

    @pytest.mark.asyncio
    async def test_query_database_page_size_limit(self, notion_client):
        """Test database query respects max page size of 100"""
        with patch.object(
            notion_client, "_call_mcp", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = {"results": []}  # Empty results list

            # Request more than 100
            await notion_client.query_database("test-db-id", page_size=200)

            # Verify page_size was capped at 100
            call_args = mock_call.call_args
            assert call_args.kwargs["data"]["page_size"] == 100
