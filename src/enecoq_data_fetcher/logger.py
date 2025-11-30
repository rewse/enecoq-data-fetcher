"""Logging configuration for enecoQ data fetcher."""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """Set up logger with console and optional file handlers.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to log file. If None, no file logging.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("enecoq_data_fetcher")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Add sensitive data filter to logger
    sensitive_filter = SensitiveDataFilter()
    logger.addFilter(sensitive_filter)
    
    # Console handler - INFO level and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler - only if log_file is specified
    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Set log level based on parameter
    level = getattr(logging, log_level.upper(), logging.INFO)
    console_handler.setLevel(level)
    
    return logger


def get_logger() -> logging.Logger:
    """Get the configured logger instance.
    
    Returns:
        Logger instance.
    """
    return logging.getLogger("enecoq_data_fetcher")


class SensitiveDataFilter(logging.Filter):
    """Filter to prevent sensitive data from being logged."""
    
    def __init__(self):
        """Initialize the filter."""
        super().__init__()
        self.sensitive_keys = ["password", "passwd", "pwd", "secret", "token"]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to remove sensitive data.
        
        Args:
            record: Log record to filter.
            
        Returns:
            True to allow the record, False to block it.
        """
        # Check if message contains sensitive keywords
        message_lower = record.getMessage().lower()
        for key in self.sensitive_keys:
            if key in message_lower:
                # Mask the sensitive data
                record.msg = self._mask_sensitive_data(str(record.msg))
        return True
    
    def _mask_sensitive_data(self, message: str) -> str:
        """Mask sensitive data in the message.
        
        Args:
            message: Original message.
            
        Returns:
            Message with sensitive data masked.
        """
        # Simple masking - replace potential sensitive values
        for key in self.sensitive_keys:
            if key in message.lower():
                # Find and mask the value after the key
                parts = message.split(":")
                if len(parts) > 1:
                    return f"{parts[0]}: ****"
        return message
