"""
Unit tests for main Cloud Functions entry point
"""

import json
from unittest.mock import Mock, patch

import pytest
from flask import Request

from src.main import _initialize_services, health_check, wbs_create


class TestInitializeServices:
    """Tests for _initialize_services function"""

    def test_initialize_services_returns_dict(self):
        """Test that _initialize_services returns services dict"""
        with patch("src.main._services", None):
            with patch("src.main._logger", None):
                services = _initialize_services()

                assert isinstance(services, dict)
                assert "logger" in services
                assert "config" in services
                assert "wbs_service" in services

    def test_initialize_services_caches_result(self):
        """Test that _initialize_services caches services"""
        with patch("src.main._services", None):
            with patch("src.main._logger", None):
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

    def test_wbs_create_options_request(self):
        """Test OPTIONS request (CORS preflight)"""
        mock_request = Mock(spec=Request)
        mock_request.method = "OPTIONS"
        mock_request.path = "/wbs-create"

        response = wbs_create(mock_request)

        assert response.status_code == 204
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
        assert "POST" in response.headers.get("Access-Control-Allow-Methods")

    def test_wbs_create_get_method_not_allowed(self):
        """Test GET request returns 405 Method Not Allowed"""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/wbs-create"

        response = wbs_create(mock_request)

        assert response.status_code == 405
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data["success"] is False
        assert "GET" in response_data["error_message"]

    def test_wbs_create_invalid_json(self):
        """Test invalid JSON returns 400 Bad Request"""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/wbs-create"
        mock_request.get_json = Mock(return_value=None)

        response = wbs_create(mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data["success"] is False
        assert "Invalid JSON" in response_data["error_message"]

    def test_wbs_create_validation_error(self):
        """Test request validation error returns 400"""
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

    def test_wbs_create_valid_request_returns_200(self):
        """Test valid request returns 200 OK"""
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

    def test_wbs_create_valid_request_with_new_tasks(self):
        """Test valid request with new_tasks_text"""
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

    def test_wbs_create_cors_headers(self):
        """Test CORS headers are set correctly"""
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
