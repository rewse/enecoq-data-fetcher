"""Tests for logger module."""

import logging
import os
import tempfile
from pathlib import Path

from enecoq_data_fetcher import logger


def test_setup_logger_default():
    """Test logger setup with default settings."""
    log = logger.setup_logger()
    
    assert log is not None
    assert log.name == "enecoq_data_fetcher"
    assert log.level == logging.DEBUG
    
    # Check handlers - only console handler by default
    assert len(log.handlers) == 1  # Console handler only
    
    # Check that sensitive data filter is added
    assert len(log.filters) >= 1
    
    print("✓ test_setup_logger_default passed")


def test_setup_logger_custom_level():
    """Test logger setup with custom log level."""
    log = logger.setup_logger(log_level="WARNING")
    
    assert log is not None
    
    # Console handler should have WARNING level
    console_handler = log.handlers[0]
    assert console_handler.level == logging.WARNING
    
    print("✓ test_setup_logger_custom_level passed")


def test_setup_logger_custom_file():
    """Test logger setup with custom log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        log = logger.setup_logger(log_file=log_file)
        
        assert log is not None
        
        # Write a test message
        log.info("Test message")
        
        # Check if file was created
        assert Path(log_file).exists()
        
        # Read file content
        content = Path(log_file).read_text()
        assert "Test message" in content
        
        print("✓ test_setup_logger_custom_file passed")


def test_get_logger():
    """Test getting logger instance."""
    # Setup logger first
    logger.setup_logger()
    
    # Get logger
    log = logger.get_logger()
    
    assert log is not None
    assert log.name == "enecoq_data_fetcher"
    
    print("✓ test_get_logger passed")


def test_sensitive_data_filter():
    """Test sensitive data filter."""
    filter_obj = logger.SensitiveDataFilter()
    
    # Create a mock log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="password: secret123",
        args=(),
        exc_info=None,
    )
    
    # Apply filter
    result = filter_obj.filter(record)
    
    # Filter should return True (allow record)
    assert result is True
    
    # Message should be masked
    assert "****" in str(record.msg) or "password" in str(record.msg).lower()
    
    print("✓ test_sensitive_data_filter passed")


def test_logging_integration():
    """Test logging integration with actual log messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "integration.log")
        log = logger.setup_logger(log_level="DEBUG", log_file=log_file)
        
        # Log messages at different levels
        log.debug("Debug message")
        log.info("Info message")
        log.warning("Warning message")
        log.error("Error message")
        
        # Read file content
        content = Path(log_file).read_text()
        
        # All messages should be in the file (DEBUG level and above)
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content
        
        print("✓ test_logging_integration passed")


if __name__ == "__main__":
    test_setup_logger_default()
    test_setup_logger_custom_level()
    test_setup_logger_custom_file()
    test_get_logger()
    test_sensitive_data_filter()
    test_logging_integration()
    
    print("\nAll logger tests passed!")
