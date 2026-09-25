"""Logging configuration for enecoQ data fetcher."""

import logging
import pathlib
import sys
from collections.abc import Iterable
from typing import Optional

LOGGER_NAME = "enecoq_data_fetcher"

# Replacement for secret values in log messages
MASK = "****"


class _StderrHandler(logging.StreamHandler):
    """Writes to sys.stderr as it is at emit time.

    A plain StreamHandler keeps the stream it was created with, so after
    sys.stderr is replaced (as click.testing.CliRunner does) it writes to a
    closed stream.
    """

    def __init__(self) -> None:
        """Initialize the handler."""
        super().__init__(sys.stderr)

    @property
    def stream(self):
        """Return the current sys.stderr."""
        return sys.stderr

    @stream.setter
    def stream(self, value) -> None:
        """Ignore assignments; the stream is always sys.stderr."""


class SensitiveDataFilter(logging.Filter):
    """Replaces known secret values in log messages with a mask."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        """Initialize the filter.

        Args:
            secrets: Values that must never appear in logs, such as the
                enecoQ password. Empty values are ignored.
        """
        super().__init__()
        # Longer secrets first, so one that contains another is fully masked.
        self._secrets = sorted(
            (secret for secret in secrets if secret), key=len, reverse=True
        )

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask secrets in the formatted message of a record.

        Args:
            record: Log record to filter.

        Returns:
            Always True, so the record is still emitted.
        """
        if not self._secrets:
            return True
        message = record.getMessage()
        masked = message
        for secret in self._secrets:
            masked = masked.replace(secret, MASK)
        if masked != message:
            # The secret may be in record.args, so store the masked result
            # as a message that needs no further formatting.
            record.msg = masked
            record.args = None
        return True


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    secrets: Iterable[str] = (),
) -> logging.Logger:
    """Set up the package logger with console and optional file handlers.

    Calling this again replaces the previous handlers and filter.

    Args:
        log_level: Console log level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to a log file that receives DEBUG and above.
        secrets: Values to mask in every log message.

    Returns:
        Configured logger instance.
    """
    log = logging.getLogger(LOGGER_NAME)
    log.setLevel(logging.DEBUG)

    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()
    for existing_filter in list(log.filters):
        log.removeFilter(existing_filter)
    log.addFilter(SensitiveDataFilter(secrets))

    # Logs go to stderr so they never mix with JSON on stdout.
    console_handler = _StderrHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    log.addHandler(console_handler)

    if log_file is not None:
        pathlib.Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        log.addHandler(file_handler)

    return log


def get_logger() -> logging.Logger:
    """Get the package logger.

    Returns:
        Logger instance.
    """
    return logging.getLogger(LOGGER_NAME)
