"""
Unit tests for URLParser
"""

import pytest

from src.models.enums import ServiceType
from src.processors.url_parser import URLParser


class TestURLParser:
    """Tests for URLParser class"""

    @pytest.fixture
    def url_parser(self):
        """Create URLParser instance"""
        return URLParser()

    def test_parse_backlog_url(self, url_parser):
        """Test parsing Backlog URL"""
        url = "https://example.backlog.com/view/PROJ-123"
        result = url_parser.parse_service_type(url)
        assert result == ServiceType.BACKLOG

    def test_parse_backlog_jp_url(self, url_parser):
        """Test parsing Backlog JP URL"""
        url = "https://example.backlog.jp/wiki/PROJ"
        result = url_parser.parse_service_type(url)
        assert result == ServiceType.BACKLOG

    def test_parse_notion_url(self, url_parser):
        """Test parsing Notion URL"""
        url = "https://www.notion.so/workspace/Page-abc123"
        result = url_parser.parse_service_type(url)
        assert result == ServiceType.NOTION

    def test_parse_notion_short_url(self, url_parser):
        """Test parsing short Notion URL"""
        url = "https://notion.so/abc123def456"
        result = url_parser.parse_service_type(url)
        assert result == ServiceType.NOTION

    def test_parse_invalid_url_raises_error(self, url_parser):
        """Test parsing invalid URL raises ValueError"""
        url = "https://example.com/unknown"
        with pytest.raises(ValueError, match="サポートされていないURLです"):
            url_parser.parse_service_type(url)

    def test_parse_empty_url_raises_error(self, url_parser):
        """Test parsing empty URL raises ValueError"""
        with pytest.raises(ValueError):
            url_parser.parse_service_type("")

    def test_parse_malformed_url_raises_error(self, url_parser):
        """Test parsing malformed URL raises ValueError"""
        with pytest.raises(ValueError):
            url_parser.parse_service_type("not a url")

    def test_validate_url_valid(self, url_parser):
        """Test validate_url with valid URL"""
        url = "https://example.com/path"
        assert url_parser.validate_url(url) is True

    def test_validate_url_invalid(self, url_parser):
        """Test validate_url with invalid URL"""
        with pytest.raises(ValueError):
            url_parser.validate_url("invalid")

    def test_validate_url_empty(self, url_parser):
        """Test validate_url with empty string"""
        with pytest.raises(ValueError):
            url_parser.validate_url("")
