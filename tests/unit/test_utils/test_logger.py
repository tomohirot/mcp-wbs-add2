"""
Unit tests for Logger
"""

import logging
from unittest.mock import Mock, patch


from src.utils.logger import Logger, get_logger


class TestLoggerInit:
    """Tests for Logger initialization"""

    def test_init_with_request_id(self):
        """Test initialization with request_id"""
        logger = Logger(request_id="test-123")
        assert logger.request_id == "test-123"
        assert logger.logger.name == "wbs-creation"

    def test_init_with_custom_name(self):
        """Test initialization with custom name"""
        logger = Logger(request_id="test-456", name="custom-logger")
        assert logger.request_id == "test-456"
        assert logger.logger.name == "custom-logger"

    def test_init_configures_handler(self):
        """Test that initialization configures stream handler"""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger

            logger = Logger(request_id="test-789")

            # Verify handler was added
            assert mock_logger.addHandler.called
            mock_logger.setLevel.assert_called_with(logging.INFO)


class TestLoggerFormatLog:
    """Tests for _format_log method"""

    def test_format_log_basic(self):
        """Test basic log formatting"""
        logger = Logger(request_id="req-001")
        log_data = logger._format_log("Test message")

        assert log_data["message"] == "Test message"
        assert log_data["request_id"] == "req-001"
        assert "timestamp" in log_data

    def test_format_log_with_kwargs(self):
        """Test log formatting with additional fields"""
        logger = Logger(request_id="req-002")
        log_data = logger._format_log("Test", user_id=123, action="login")

        assert log_data["message"] == "Test"
        assert log_data["user_id"] == 123
        assert log_data["action"] == "login"

    def test_format_log_filters_sensitive_data(self):
        """Test that sensitive data is filtered out"""
        logger = Logger(request_id="req-003")
        log_data = logger._format_log(
            "Login attempt",
            username="user123",
            password="secret123",
            api_key="key123",
            token="token123",
            secret="secret123",
        )

        assert log_data["username"] == "user123"
        assert "password" not in log_data
        assert "api_key" not in log_data
        assert "token" not in log_data
        assert "secret" not in log_data


class TestLoggerInfoMethod:
    """Tests for info logging method"""

    def test_info_logs_message(self):
        """Test info logging"""
        logger = Logger(request_id="req-004")

        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Info message", key="value")

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert call_args["message"] == "Info message"
            assert call_args["key"] == "value"


class TestLoggerErrorMethod:
    """Tests for error logging method"""

    def test_error_logs_message(self):
        """Test error logging without exception"""
        logger = Logger(request_id="req-005")

        with patch.object(logger.logger, "error") as mock_error:
            logger.error("Error message", key="value")

            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert call_args["message"] == "Error message"
            assert call_args["key"] == "value"

    def test_error_logs_with_exception(self):
        """Test error logging with exception"""
        logger = Logger(request_id="req-006")

        with patch.object(logger.logger, "error") as mock_error:
            test_exception = ValueError("Test error")
            logger.error("Error occurred", error=test_exception)

            call_args = mock_error.call_args[0][0]
            assert call_args["message"] == "Error occurred"
            assert call_args["error_type"] == "ValueError"
            assert call_args["error_message"] == "Test error"


class TestLoggerWarningMethod:
    """Tests for warning logging method"""

    def test_warning_logs_message(self):
        """Test warning logging"""
        logger = Logger(request_id="req-007")

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.warning("Warning message", severity="medium")

            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0][0]
            assert call_args["message"] == "Warning message"
            assert call_args["severity"] == "medium"


class TestLoggerDebugMethod:
    """Tests for debug logging method"""

    def test_debug_logs_message(self):
        """Test debug logging"""
        logger = Logger(request_id="req-008")

        with patch.object(logger.logger, "debug") as mock_debug:
            logger.debug("Debug message", detail="test")

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args[0][0]
            assert call_args["message"] == "Debug message"
            assert call_args["detail"] == "test"


class TestGetLogger:
    """Tests for get_logger factory function"""

    def test_get_logger_returns_logger_instance(self):
        """Test get_logger returns Logger instance"""
        logger = get_logger(request_id="req-009")
        assert isinstance(logger, Logger)
        assert logger.request_id == "req-009"

    def test_get_logger_with_custom_name(self):
        """Test get_logger with custom name"""
        logger = get_logger(request_id="req-010", name="custom")
        assert logger.logger.name == "custom"
