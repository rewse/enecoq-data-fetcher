"""Configuration management for enecoQ data fetcher."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class Config:
    """Configuration for enecoQ data fetcher.

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Path to log file.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        user_agent: User agent string for HTTP requests.
    """

    log_level: str = "INFO"
    log_file: str = "logs/enecoq.log"
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/26.0 Safari/605.1.15"
    )

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Config instance with values from file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If YAML library is not available or file is invalid.
        """
        if not YAML_AVAILABLE:
            raise ValueError(
                "PyYAML is not installed. "
                "Install it with: pip install pyyaml"
            )

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            config_data = {}

        return cls(
            log_level=config_data.get("log_level", cls.log_level),
            log_file=config_data.get("log_file", cls.log_file),
            timeout=config_data.get("timeout", cls.timeout),
            max_retries=config_data.get("max_retries", cls.max_retries),
            user_agent=config_data.get("user_agent", cls.user_agent),
        )

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        log_level: Optional[str] = None,
    ) -> "Config":
        """Load configuration with optional overrides.

        This method loads configuration from a file (if provided and exists),
        then applies command-line argument overrides.

        Args:
            config_path: Optional path to configuration file.
            log_level: Optional log level override from command line.

        Returns:
            Config instance with merged values.
        """
        # Start with default config
        config = cls()

        # Load from file if provided and exists
        if config_path and os.path.exists(config_path):
            try:
                config = cls.from_file(config_path)
            except (ValueError, FileNotFoundError) as e:
                # If file loading fails, use defaults
                # This allows the tool to work without YAML library
                pass

        # Apply command-line overrides
        if log_level is not None:
            config.log_level = log_level

        return config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration.
        """
        return {
            "log_level": self.log_level,
            "log_file": self.log_file,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "user_agent": self.user_agent,
        }
