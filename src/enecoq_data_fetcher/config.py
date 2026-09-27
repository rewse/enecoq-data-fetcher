"""Configuration management for enecoQ data fetcher."""

import dataclasses
from typing import Any, Optional

import yaml

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def _require_int(name: str, value: Any, minimum: int) -> None:
    """Check that a config value is an integer of at least minimum.

    Args:
        name: Config key, used in the error message.
        value: Value to check.
        minimum: Smallest accepted value.

    Raises:
        ValueError: If the value is not an integer or is below minimum.
    """
    # bool is a subclass of int, but "true" is never a valid count.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an integer: %r" % (name, value))
    if value < minimum:
        raise ValueError("%s must be %d or greater: %r" % (name, minimum, value))


@dataclasses.dataclass
class Config:
    """Configuration for enecoQ data fetcher.

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Path to log file, or None to log only to the console.
        timeout: Browser operation timeout in seconds.
        max_retries: Number of retries after the first failed attempt.
        user_agent: User agent string for the browser.
    """

    log_level: str = "INFO"
    log_file: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/26.0 Safari/605.1.15"
    )

    def __post_init__(self) -> None:
        """Validate the values and normalize the log level.

        Raises:
            ValueError: If a value has the wrong type or is out of range.
        """
        if (
            not isinstance(self.log_level, str)
            or self.log_level.upper() not in LOG_LEVELS
        ):
            raise ValueError(
                "log_level must be one of %s: %r"
                % (", ".join(LOG_LEVELS), self.log_level)
            )
        self.log_level = self.log_level.upper()
        if self.log_file is not None and not isinstance(self.log_file, str):
            raise ValueError("log_file must be a string: %r" % (self.log_file,))
        _require_int("timeout", self.timeout, minimum=1)
        _require_int("max_retries", self.max_retries, minimum=0)
        if not isinstance(self.user_agent, str) or not self.user_agent:
            raise ValueError("user_agent must be a non-empty string")

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from a YAML file.

        Args:
            config_path: Path to the configuration file.

        Returns:
            Config with the values from the file and defaults for the rest.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid YAML, is not a mapping,
                contains unknown keys, or contains invalid values.
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError("Config file not found: %s" % config_path) from e
        except yaml.YAMLError as e:
            raise ValueError("Invalid YAML in %s: %s" % (config_path, e)) from e

        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ValueError("Config file must contain a mapping: %s" % config_path)
        known_keys = {field.name for field in dataclasses.fields(cls)}
        unknown_keys = sorted(str(key) for key in data if key not in known_keys)
        if unknown_keys:
            raise ValueError(
                "Unknown keys in %s: %s" % (config_path, ", ".join(unknown_keys))
            )
        return cls(**data)

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
    ) -> "Config":
        """Load configuration and apply command-line overrides.

        Args:
            config_path: Optional path to a configuration file.
            log_level: Optional log level that overrides the file.
            log_file: Optional log file path that overrides the file.

        Returns:
            Config with the overrides applied.

        Raises:
            FileNotFoundError: If config_path is given but does not exist.
            ValueError: If the file or an override is invalid.
        """
        config = cls() if config_path is None else cls.from_file(config_path)
        overrides = {}
        if log_level is not None:
            overrides["log_level"] = log_level
        if log_file is not None:
            overrides["log_file"] = log_file
        # replace() runs __post_init__, so overrides are validated too.
        return dataclasses.replace(config, **overrides)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return dataclasses.asdict(self)
