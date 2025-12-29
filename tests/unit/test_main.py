"""
Unit tests for main Cloud Functions entry point
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from flask import Request

from src.main import _initialize_services, health_check, wbs_create


class TestInitializeServices:
    """Tests for _initialize_services function"""

    @patch("src.processors.document_processor.documentai")
    @patch("src.storage.firestore_client.firestore")
    @patch("src.storage.gcs_client.storage")
    def test_initialize_services_returns_dict(
        self, mock_gcs_storage, mock_firestore, mock_documentai
    ):
        """Test that _initialize_services returns services dict"""
        # Reset global variables to force re-initialization
        import src.main

        src.main._services = None
        src.main._logger = None

        # Mock GCP clients to avoid authentication errors
        mock_documentai.DocumentProcessorServiceClient.return_value = Mock()
        mock_firestore.Client.return_value = Mock()
        mock_gcs_storage.Client.return_value = Mock()

        # Call _initialize_services
        services = _initialize_services()

        assert isinstance(services, dict)
        assert "logger" in services
        assert "config" in services
        assert "wbs_service" in services

        # Verify the services are not None
        assert services["logger"] is not None
        assert services["config"] is not None
        assert services["wbs_service"] is not None

    @patch("src.processors.document_processor.documentai")
    @patch("src.storage.firestore_client.firestore")
    @patch("src.storage.gcs_client.storage")
    def test_initialize_services_caches_result(
        self, mock_gcs_storage, mock_firestore, mock_documentai
    ):
        """Test that _initialize_services caches services"""
        # Mock GCP clients to avoid authentication errors
        mock_documentai.DocumentProcessorServiceClient.return_value = Mock()
        mock_firestore.Client.return_value = Mock()
        mock_gcs_storage.Client.return_value = Mock()

        # Call _initialize_services twice
        services1 = _initialize_services()
        services2 = _initialize_services()

        # Should return the same instance (cached)
        assert services1 is services2


class TestHealthCheck:
    """Tests for health_check endpoint"""

    def test_health_check_returns_200(self):
        """Test health check returns 200 OK"""
        mock_request = Mock(spec=Request)

        response = health_check(mock_request)

        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"

    def test_health_check_returns_healthy_status(self):
        """Test health check returns healthy status"""
        mock_request = Mock(spec=Request)

        response = health_check(mock_request)

        response_data = json.loads(response.get_data(as_text=True))
        assert response_data["status"] == "healthy"
        assert "server" in response_data

    def test_health_check_includes_server_metadata(self):
        """Test health check includes server metadata"""
        mock_request = Mock(spec=Request)

        response = health_check(mock_request)

        response_data = json.loads(response.get_data(as_text=True))
        server_metadata = response_data["server"]

        assert "name" in server_metadata
        assert "version" in server_metadata
        assert "capabilities" in server_metadata


class TestWBSCreate:
    """Tests for wbs_create endpoint"""

    @patch("src.main._initialize_services")
    def test_wbs_create_options_request(self, mock_init):
        """Test OPTIONS request (CORS preflight)"""
        # Mock services (not used in OPTIONS)
        mock_logger = Mock()
        mock_init.return_value = {
            "logger": mock_logger,
            "config": Mock(),
            "wbs_service": Mock(),
        }

        mock_request = Mock(spec=Request)
        mock_request.method = "OPTIONS"
        mock_request.path = "/wbs-create"

        response = wbs_create(mock_request)

        assert response.status_code == 204
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
        assert "POST" in response.headers.get("Access-Control-Allow-Methods")

    @patch("src.main._initialize_services")
    def test_wbs_create_get_method_not_allowed(self, mock_init):
        """Test GET request returns 405 Method Not Allowed"""
        # Mock services
        mock_logger = Mock()
        mock_init.return_value = {
            "logger": mock_logger,
            "config": Mock(),
            "wbs_service": Mock(),
        }

        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/wbs-create"

        response = wbs_create(mock_request)

        assert response.status_code == 405
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data["success"] is False
        assert "GET" in response_data["error_message"]

    @patch("src.main._initialize_services")
    def test_wbs_create_invalid_json(self, mock_init):
        """Test invalid JSON returns 400 Bad Request"""
        # Mock services
        mock_logger = Mock()
        mock_init.return_value = {
            "logger": mock_logger,
            "config": Mock(),
            "wbs_service": Mock(),
        }

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/wbs-create"
        mock_request.get_json = Mock(return_value=None)

        response = wbs_create(mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data["success"] is False
        assert "Invalid JSON" in response_data["error_message"]

    @patch("src.main._initialize_services")
    def test_wbs_create_validation_error(self, mock_init):
        """Test request validation error returns 400"""
        # Mock services
        mock_logger = Mock()
        mock_init.return_value = {
            "logger": mock_logger,
            "config": Mock(),
            "wbs_service": Mock(),
        }

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/wbs-create"
        mock_request.get_json = Mock(
            return_value={
                # Missing required fields
                "invalid_field": "value"
            }
        )

        response = wbs_create(mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data["success"] is False
        assert "validation error" in response_data["error_message"]

    @patch("src.mcp.handlers.handle_create_wbs")
    @patch("src.main._initialize_services")
    def test_wbs_create_valid_request_returns_200(self, mock_init, mock_handler):
        """Test valid request returns 200 OK"""
        # Mock services
        mock_logger = Mock()
        mock_wbs_service = Mock()
        mock_init.return_value = {
            "logger": mock_logger,
            "config": Mock(),
            "wbs_service": mock_wbs_service,
        }

        # Mock successful response from handler
        from src.mcp.schemas import CreateWBSResponse

        mock_response = CreateWBSResponse(
            success=True, registered_tasks=[], failed_tasks=[]
        )
        # handle_create_wbs is async, so we need AsyncMock
        mock_handler.return_value = mock_response

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/wbs-create"
        mock_request.get_json = Mock(
            return_value={
                "template_url": "https://test.backlog.com/view/PROJ-1",
                "project_key": "PROJ",
            }
        )

        response = wbs_create(mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data["success"] is True

    @patch("src.mcp.handlers.handle_create_wbs")
    @patch("src.main._initialize_services")
    def test_wbs_create_valid_request_with_new_tasks(self, mock_init, mock_handler):
        """Test valid request with new_tasks_text"""
        # Mock services
        mock_logger = Mock()
        mock_wbs_service = Mock()
        mock_init.return_value = {
            "logger": mock_logger,
            "config": Mock(),
            "wbs_service": mock_wbs_service,
        }

        # Mock successful response from handler
        from src.mcp.schemas import CreateWBSResponse

        mock_response = CreateWBSResponse(
            success=True, registered_tasks=[], failed_tasks=[]
        )
        # handle_create_wbs is async, so we need AsyncMock
        mock_handler.return_value = mock_response

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/wbs-create"
        mock_request.get_json = Mock(
            return_value={
                "template_url": "https://test.backlog.com/view/PROJ-1",
                "new_tasks_text": "- Task 1 | priority: 高",
                "project_key": "PROJ",
            }
        )

        response = wbs_create(mock_request)

        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"

    @patch("src.mcp.handlers.handle_create_wbs")
    @patch("src.main._initialize_services")
    def test_wbs_create_cors_headers(self, mock_init, mock_handler):
        """Test CORS headers are set correctly"""
        # Mock services
        mock_logger = Mock()
        mock_wbs_service = Mock()
        mock_init.return_value = {
            "logger": mock_logger,
            "config": Mock(),
            "wbs_service": mock_wbs_service,
        }

        # Mock successful response from handler
        from src.mcp.schemas import CreateWBSResponse

        mock_response = CreateWBSResponse(
            success=True, registered_tasks=[], failed_tasks=[]
        )
        # handle_create_wbs is async, so we need AsyncMock
        mock_handler.return_value = mock_response

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/wbs-create"
        mock_request.get_json = Mock(
            return_value={
                "template_url": "https://test.backlog.com/view/PROJ-1",
                "project_key": "PROJ",
            }
        )

        response = wbs_create(mock_request)

        assert response.headers.get("Access-Control-Allow-Origin") == "*"
        assert "POST" in response.headers.get("Access-Control-Allow-Methods")

    @patch("src.main._initialize_services")
    def test_wbs_create_service_initialization_error(self, mock_init):
        """Test that service initialization error propagates (not caught)"""
        mock_init.side_effect = Exception("Service init failed")

        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/wbs-create"
        mock_request.get_json = Mock(
            return_value={
                "template_url": "https://test.backlog.com/view/PROJ-1",
                "project_key": "PROJ",
            }
        )

        # Service initialization errors are not caught (happens before try block)
        with pytest.raises(Exception, match="Service init failed"):
            wbs_create(mock_request)
