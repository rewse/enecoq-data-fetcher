"""Tests for logger module."""

import io
import logging
import os
import sys
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


def test_sensitive_data_filter_masks_secret_in_args():
    """Test that a secret passed as a format argument is masked."""
    filter_obj = logger.SensitiveDataFilter(["s3cr3t"])
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Login with %s failed after %d tries",
        args=("s3cr3t", 3),
        exc_info=None,
    )

    assert filter_obj.filter(record) is True
    assert record.getMessage() == "Login with **** failed after 3 tries"

    print("✓ test_sensitive_data_filter_masks_secret_in_args passed")


def test_sensitive_data_filter_keeps_other_messages():
    """Test that messages without secrets keep their format arguments."""
    filter_obj = logger.SensitiveDataFilter(["s3cr3t"])
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="password field: %s",
        args=("filled",),
        exc_info=None,
    )

    assert filter_obj.filter(record) is True
    assert record.getMessage() == "password field: filled"
    assert record.args == ("filled",)

    print("✓ test_sensitive_data_filter_keeps_other_messages passed")


def test_setup_logger_masks_secrets_in_file():
    """Test that setup_logger masks the given secrets in the log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "secret.log")
        log = logger.setup_logger(log_file=log_file, secrets=["s3cr3t"])

        log.error("Request failed: %s", "token=s3cr3t")
        for handler in log.handlers:
            handler.flush()

        content = Path(log_file).read_text()
        assert "s3cr3t" not in content
        assert "token=****" in content

    print("✓ test_setup_logger_masks_secrets_in_file passed")


def test_setup_logger_does_not_duplicate_filters():
    """Test that calling setup_logger twice keeps a single filter."""
    logger.setup_logger(secrets=["one"])
    log = logger.setup_logger(secrets=["two"])

    assert len(log.filters) == 1
    assert len(log.handlers) == 1

    print("✓ test_setup_logger_does_not_duplicate_filters passed")


def test_console_handler_follows_current_stderr():
    """Test that console logs go to sys.stderr as it is when emitting."""
    log = logger.setup_logger()
    original_stderr = sys.stderr
    replaced = io.StringIO()
    try:
        sys.stderr = replaced
        log.warning("After replacing stderr")
    finally:
        sys.stderr = original_stderr

    assert "After replacing stderr" in replaced.getvalue()
    print("✓ test_console_handler_follows_current_stderr passed")


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


def test_setup_logger_masks_secrets_in_traceback():
    """Test that a secret in an exception's traceback is masked in the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "traceback.log")
        log = logger.setup_logger(log_file=log_file, secrets=["hunter2"])

        try:
            raise RuntimeError("bad password hunter2")
        except RuntimeError:
            log.error("Unexpected error", exc_info=True)
        for handler in log.handlers:
            handler.flush()

        content = Path(log_file).read_text()
        assert "hunter2" not in content, content
        assert "RuntimeError: bad password ****" in content

    print("✓ test_setup_logger_masks_secrets_in_traceback passed")


if __name__ == "__main__":
    test_setup_logger_default()
    test_setup_logger_custom_level()
    test_setup_logger_custom_file()
    test_get_logger()
    test_sensitive_data_filter_masks_secret_in_args()
    test_sensitive_data_filter_keeps_other_messages()
    test_setup_logger_masks_secrets_in_file()
    test_setup_logger_does_not_duplicate_filters()
    test_console_handler_follows_current_stderr()
    test_setup_logger_masks_secrets_in_traceback()
    test_logging_integration()

    print("\nAll logger tests passed!")
