"""
Unit tests for validators module
"""

import pytest

from src.utils.validators import (validate_backlog_url, validate_notion_url,
                                  validate_project_key, validate_url)


class TestValidateUrl:
    """Tests for validate_url function"""

    def test_valid_https_url(self):
        """Test valid HTTPS URL"""
        assert validate_url("https://example.com") is True

    def test_valid_http_url(self):
        """Test valid HTTP URL"""
        assert validate_url("http://example.com") is True

    def test_url_with_path(self):
        """Test URL with path"""
        assert validate_url("https://example.com/path/to/page") is True

    def test_url_with_query(self):
        """Test URL with query parameters"""
        assert validate_url("https://example.com?param=value") is True

    def test_invalid_url_no_scheme(self):
        """Test invalid URL without scheme"""
        with pytest.raises(ValueError):
            validate_url("example.com")

    def test_invalid_url_empty(self):
        """Test empty URL"""
        with pytest.raises(ValueError):
            validate_url("")

    def test_invalid_url_malformed(self):
        """Test malformed URL"""
        with pytest.raises(ValueError):
            validate_url("not a url")


class TestValidateBacklogUrl:
    """Tests for validate_backlog_url function"""

    def test_valid_backlog_url(self):
        """Test valid Backlog URL"""
        url = "https://example.backlog.com/view/PROJ-123"
        assert validate_backlog_url(url) is True

    def test_valid_backlog_url_jp(self):
        """Test valid Backlog JP URL"""
        url = "https://example.backlog.jp/view/PROJ-456"
        assert validate_backlog_url(url) is True

    def test_backlog_url_with_different_path(self):
        """Test Backlog URL with different path"""
        url = "https://example.backlog.com/wiki/PROJ"
        assert validate_backlog_url(url) is True

    def test_invalid_backlog_url_wrong_domain(self):
        """Test non-Backlog URL"""
        url = "https://example.com/view/PROJ-123"
        with pytest.raises(ValueError):
            validate_backlog_url(url)

    def test_invalid_backlog_url_empty(self):
        """Test empty URL"""
        with pytest.raises(ValueError):
            validate_backlog_url("")


class TestValidateNotionUrl:
    """Tests for validate_notion_url function"""

    def test_valid_notion_url_with_id(self):
        """Test valid Notion URL with page ID"""
        url = "https://www.notion.so/workspace/Page-Title-abc123def456"
        assert validate_notion_url(url) is True

    def test_valid_notion_url_short(self):
        """Test valid short Notion URL"""
        url = "https://notion.so/abc123def456"
        assert validate_notion_url(url) is True

    def test_notion_url_with_uuid(self):
        """Test Notion URL with UUID format"""
        url = "https://www.notion.so/12345678-1234-1234-1234-123456789abc"
        assert validate_notion_url(url) is True

    def test_invalid_notion_url_wrong_domain(self):
        """Test non-Notion URL"""
        url = "https://example.com/page"
        with pytest.raises(ValueError):
            validate_notion_url(url)

    def test_invalid_notion_url_empty(self):
        """Test empty URL"""
        with pytest.raises(ValueError):
            validate_notion_url("")


class TestValidateProjectKey:
    """Tests for validate_project_key function"""

    def test_valid_project_key_uppercase(self):
        """Test valid uppercase project key"""
        assert validate_project_key("PROJ") is True

    def test_valid_project_key_mixed_case(self):
        """Test valid mixed case project key"""
        assert validate_project_key("Project") is True

    def test_valid_project_key_with_numbers(self):
        """Test valid project key with numbers"""
        assert validate_project_key("PROJ123") is True

    def test_valid_project_key_single_char(self):
        """Test valid single character project key"""
        assert validate_project_key("P") is True

    def test_valid_project_key_long(self):
        """Test valid long project key"""
        assert validate_project_key("P" * 51) is True

    def test_invalid_project_key_with_spaces(self):
        """Test project key with spaces"""
        with pytest.raises(ValueError):
            validate_project_key("PROJ KEY")

    def test_invalid_project_key_with_symbols(self):
        """Test project key with special symbols"""
        with pytest.raises(ValueError):
            validate_project_key("PROJ@123")

    def test_invalid_project_key_empty(self):
        """Test empty project key"""
        with pytest.raises(ValueError):
            validate_project_key("")
