"""
Unit tests for MasterService
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.services.master_service import (REQUIRED_CATEGORIES,
                                         REQUIRED_ISSUE_TYPES,
                                         MasterDataResult, MasterService)


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    return logger


@pytest.fixture
def mock_backlog_client():
    """Create mock Backlog client"""
    return Mock()


@pytest.fixture
def master_service(mock_backlog_client, mock_logger):
    """Create MasterService instance"""
    return MasterService(mock_backlog_client, mock_logger)


class TestMasterDataResult:
    """Tests for MasterDataResult class"""

    def test_init(self):
        """Test MasterDataResult initialization"""
        result = MasterDataResult()
        assert result.created_issue_types == []
        assert result.created_categories == []
        assert result.created_custom_fields == []
        assert result.errors == []

    def test_success_with_no_errors(self):
        """Test success property returns True when no errors"""
        result = MasterDataResult()
        result.created_issue_types = ["課題"]
        assert result.success is True

    def test_success_with_errors(self):
        """Test success property returns False when errors exist"""
        result = MasterDataResult()
        result.errors = ["Error 1"]
        assert result.success is False

    def test_total_created(self):
        """Test total_created counts all created items"""
        result = MasterDataResult()
        result.created_issue_types = ["課題", "リスク"]
        result.created_categories = ["事前準備", "要件定義"]
        result.created_custom_fields = ["インプット"]

        assert result.total_created == 5


class TestMasterServiceInit:
    """Tests for MasterService initialization"""

    def test_init(self, mock_backlog_client, mock_logger):
        """Test MasterService initialization"""
        service = MasterService(mock_backlog_client, mock_logger)
        assert service.backlog_client == mock_backlog_client
        assert service.logger == mock_logger


class TestMasterServiceSetupMasterData:
    """Tests for setup_master_data method"""

    @pytest.mark.asyncio
    async def test_setup_all_successful(self, master_service, mock_backlog_client):
        """Test successful master data setup"""
        # Mock all methods to return empty lists (nothing created, all exist)
        master_service._ensure_issue_types = AsyncMock(return_value=[])
        master_service._ensure_categories = AsyncMock(return_value=[])
        master_service._ensure_custom_fields = AsyncMock(return_value=[])

        result = await master_service.setup_master_data("TEST_PROJECT")

        assert result.success is True
        assert result.total_created == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_setup_creates_items(self, master_service):
        """Test setup when items need to be created"""
        master_service._ensure_issue_types = AsyncMock(return_value=["課題"])
        master_service._ensure_categories = AsyncMock(
            return_value=["事前準備", "要件定義"]
        )
        master_service._ensure_custom_fields = AsyncMock(return_value=["インプット"])

        result = await master_service.setup_master_data("TEST_PROJECT")

        assert result.success is True
        assert result.total_created == 4
        assert len(result.created_issue_types) == 1
        assert len(result.created_categories) == 2
        assert len(result.created_custom_fields) == 1

    @pytest.mark.asyncio
    async def test_setup_with_issue_type_error(self, master_service):
        """Test setup handles issue type errors"""
        master_service._ensure_issue_types = AsyncMock(
            side_effect=Exception("API error")
        )
        master_service._ensure_categories = AsyncMock(return_value=[])
        master_service._ensure_custom_fields = AsyncMock(return_value=[])

        result = await master_service.setup_master_data("TEST_PROJECT")

        assert result.success is False
        assert len(result.errors) == 1
        assert "Failed to setup issue types" in result.errors[0]

    @pytest.mark.asyncio
    async def test_setup_with_category_error(self, master_service):
        """Test setup handles category errors"""
        master_service._ensure_issue_types = AsyncMock(return_value=[])
        master_service._ensure_categories = AsyncMock(
            side_effect=Exception("Category API error")
        )
        master_service._ensure_custom_fields = AsyncMock(return_value=[])

        result = await master_service.setup_master_data("TEST_PROJECT")

        assert result.success is False
        assert len(result.errors) == 1
        assert "Failed to setup categories" in result.errors[0]

    @pytest.mark.asyncio
    async def test_setup_with_custom_field_error(self, master_service):
        """Test setup handles custom field errors"""
        master_service._ensure_issue_types = AsyncMock(return_value=[])
        master_service._ensure_categories = AsyncMock(return_value=[])
        master_service._ensure_custom_fields = AsyncMock(
            side_effect=Exception("Custom field error")
        )

        result = await master_service.setup_master_data("TEST_PROJECT")

        assert result.success is False
        assert len(result.errors) == 1
        assert "Failed to setup custom fields" in result.errors[0]

    @pytest.mark.asyncio
    async def test_setup_with_multiple_errors(self, master_service):
        """Test setup handles multiple errors"""
        master_service._ensure_issue_types = AsyncMock(side_effect=Exception("Error 1"))
        master_service._ensure_categories = AsyncMock(side_effect=Exception("Error 2"))
        master_service._ensure_custom_fields = AsyncMock(
            side_effect=Exception("Error 3")
        )

        result = await master_service.setup_master_data("TEST_PROJECT")

        assert result.success is False
        assert len(result.errors) == 3


class TestMasterServiceEnsureIssueTypes:
    """Tests for _ensure_issue_types method"""

    @pytest.mark.asyncio
    async def test_ensure_issue_types_all_exist(
        self, master_service, mock_backlog_client
    ):
        """Test when all required issue types already exist"""
        # Mock existing types - properly set .name attribute
        type1 = Mock()
        type1.name = "課題"
        type2 = Mock()
        type2.name = "リスク"
        type3 = Mock()
        type3.name = "バグ"
        existing_types = [type1, type2, type3]

        mock_backlog_client.get_issue_types = AsyncMock(return_value=existing_types)
        mock_backlog_client.create_issue_type = AsyncMock()

        result = await master_service._ensure_issue_types("TEST_PROJECT")

        assert result == []  # Nothing created
        mock_backlog_client.get_issue_types.assert_called_once_with("TEST_PROJECT")
        mock_backlog_client.create_issue_type.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_issue_types_creates_missing(
        self, master_service, mock_backlog_client
    ):
        """Test when issue types need to be created"""
        # Mock only one existing type
        existing_types = [Mock(name="バグ")]
        mock_backlog_client.get_issue_types = AsyncMock(return_value=existing_types)
        mock_backlog_client.create_issue_type = AsyncMock()

        result = await master_service._ensure_issue_types("TEST_PROJECT")

        assert len(result) == 2
        assert "課題" in result
        assert "リスク" in result
        assert mock_backlog_client.create_issue_type.call_count == 2


class TestMasterServiceEnsureCategories:
    """Tests for _ensure_categories method"""

    @pytest.mark.asyncio
    async def test_ensure_categories_all_exist(
        self, master_service, mock_backlog_client
    ):
        """Test when all required categories already exist"""
        # Properly set .name attribute
        cat_names = [
            "事前準備",
            "要件定義",
            "基本設計",
            "実装",
            "テスト",
            "リリース",
            "納品",
        ]
        existing_categories = []
        for cat_name in cat_names:
            cat = Mock()
            cat.name = cat_name
            existing_categories.append(cat)

        mock_backlog_client.get_categories = AsyncMock(return_value=existing_categories)
        mock_backlog_client.create_category = AsyncMock()

        result = await master_service._ensure_categories("TEST_PROJECT")

        assert result == []
        mock_backlog_client.get_categories.assert_called_once_with("TEST_PROJECT")
        mock_backlog_client.create_category.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_categories_creates_missing(
        self, master_service, mock_backlog_client
    ):
        """Test when categories need to be created"""
        # Mock NO existing categories
        existing_categories = []
        mock_backlog_client.get_categories = AsyncMock(return_value=existing_categories)
        mock_backlog_client.create_category = AsyncMock()

        result = await master_service._ensure_categories("TEST_PROJECT")

        # Should create all 7 required categories
        assert len(result) == 7
        assert mock_backlog_client.create_category.call_count == 7


class TestMasterServiceEnsureCustomFields:
    """Tests for _ensure_custom_fields method"""

    @pytest.mark.asyncio
    async def test_ensure_custom_fields_all_exist(
        self, master_service, mock_backlog_client
    ):
        """Test when all required custom fields already exist"""
        # Properly set .name attribute
        field1 = Mock()
        field1.name = "インプット"
        field2 = Mock()
        field2.name = "ゴール/アウトプット"
        existing_fields = [field1, field2]

        mock_backlog_client.get_custom_fields = AsyncMock(return_value=existing_fields)
        mock_backlog_client.create_custom_field = AsyncMock()

        result = await master_service._ensure_custom_fields("TEST_PROJECT")

        assert result == []
        mock_backlog_client.get_custom_fields.assert_called_once_with("TEST_PROJECT")
        mock_backlog_client.create_custom_field.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_custom_fields_creates_missing(
        self, master_service, mock_backlog_client
    ):
        """Test when custom fields need to be created"""
        # Mock NO existing custom fields
        existing_fields = []
        mock_backlog_client.get_custom_fields = AsyncMock(return_value=existing_fields)
        mock_backlog_client.create_custom_field = AsyncMock()

        result = await master_service._ensure_custom_fields("TEST_PROJECT")

        # Should create 2 required custom fields
        assert len(result) == 2
        assert "インプット" in result
        assert "ゴール/アウトプット" in result
        assert mock_backlog_client.create_custom_field.call_count == 2

    @pytest.mark.asyncio
    async def test_ensure_custom_fields_creates_partial(
        self, master_service, mock_backlog_client
    ):
        """Test when some custom fields need to be created"""
        # Mock only one existing field
        field1 = Mock()
        field1.name = "インプット"
        existing_fields = [field1]

        mock_backlog_client.get_custom_fields = AsyncMock(return_value=existing_fields)
        mock_backlog_client.create_custom_field = AsyncMock()

        result = await master_service._ensure_custom_fields("TEST_PROJECT")

        # Should create 1 missing custom field
        assert len(result) == 1
        assert "ゴール/アウトプット" in result
        assert mock_backlog_client.create_custom_field.call_count == 1


class TestMasterServiceConstants:
    """Tests for module constants"""

    def test_required_issue_types(self):
        """Test REQUIRED_ISSUE_TYPES constant"""
        assert len(REQUIRED_ISSUE_TYPES) == 2
        assert "課題" in REQUIRED_ISSUE_TYPES
        assert "リスク" in REQUIRED_ISSUE_TYPES

    def test_required_categories(self):
        """Test REQUIRED_CATEGORIES constant"""
        assert len(REQUIRED_CATEGORIES) == 7
        assert "事前準備" in REQUIRED_CATEGORIES
        assert "要件定義" in REQUIRED_CATEGORIES
        assert "基本設計" in REQUIRED_CATEGORIES
        assert "実装" in REQUIRED_CATEGORIES
        assert "テスト" in REQUIRED_CATEGORIES
        assert "リリース" in REQUIRED_CATEGORIES
        assert "納品" in REQUIRED_CATEGORIES
