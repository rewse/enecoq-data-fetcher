"""Command-line interface for enecoQ data fetcher."""

import datetime
import logging
import os
import sys
from typing import NoReturn, Optional

import click

from enecoq_data_fetcher import __version__
from enecoq_data_fetcher import config as config_module
from enecoq_data_fetcher import controller
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import logger

# Loaded when --config is not given and the file exists
DEFAULT_CONFIG_PATH = "config.yaml"

EXIT_AUTH_ERROR = 1
EXIT_FETCH_ERROR = 2
EXIT_EXPORT_ERROR = 3
EXIT_ENECOQ_ERROR = 4
EXIT_UNEXPECTED_ERROR = 5
EXIT_INVALID_ARGUMENT = 6


@click.command()
@click.version_option(version=__version__, prog_name="enecoq-data-fetcher")
@click.option(
    "--email",
    required=True,
    help="Email address for enecoQ authentication.",
)
@click.option(
    "--password",
    required=True,
    help="Password for enecoQ authentication.",
)
@click.option(
    "--period",
    type=click.Choice(["today", "month"], case_sensitive=False),
    default="month",
    help="Data period to fetch (default: month).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "console"], case_sensitive=False),
    default="json",
    help="Output format (default: json).",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(),
    default=None,
    help="Output file path for JSON format (optional).",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False),
    default=None,
    help="Configuration file path (default: config.yaml if it exists).",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default=None,
    help="Logging level (default: INFO, or from config file).",
)
@click.option(
    "--log-file",
    type=click.Path(),
    default=None,
    help="Log file path (optional, no file logging by default).",
)
def main(
    email: str,
    password: str,
    period: str,
    output_format: str,
    output_path: Optional[str],
    config_path: Optional[str],
    log_level: Optional[str],
    log_file: Optional[str],
) -> None:
    """enecoQ Data Fetcher - Fetch power usage data from enecoQ Web Service.

    This tool retrieves power usage, cost, and CO2 emission data from the
    enecoQ Web Service.

    Examples:

        \b
        # Fetch this month's data and display in console
        $ enecoq-data-fetcher --email user@example.com --password secret --format console

        \b
        # Fetch today's data and save to JSON file
        $ enecoq-data-fetcher --email user@example.com --password secret --period today --output data.json

        \b
        # Fetch with debug logging
        $ enecoq-data-fetcher --email user@example.com --password secret --log-level DEBUG

        \b
        # Use custom config file
        $ enecoq-data-fetcher --email user@example.com --password secret --config /path/to/config.yaml
    """
    log = None
    secrets = [password]
    try:
        _validate_arguments(email, password, output_format, output_path)
        config = _load_config(config_path, log_level, log_file)
        log = logger.setup_logger(
            log_level=config.log_level,
            log_file=config.log_file,
            secrets=secrets,
        )
        log.info(
            "Starting enecoQ data fetcher at %s",
            datetime.datetime.now().isoformat(),
        )
        log.debug(
            "Parameters - Period: %s, Format: %s, Config: %s",
            period, output_format, config_path,
        )
        log.debug(
            "Configuration - Log level: %s, Timeout: %s, Max retries: %s",
            config.log_level, config.timeout, config.max_retries,
        )

        enecoq_controller = controller.EnecoQController(
            email, password, config=config
        )
        enecoq_controller.fetch_power_data(
            period=period.lower(),
            output_format=output_format.lower(),
            output_path=output_path,
        )

        if output_path:
            click.echo("Data successfully exported to: %s" % output_path)
            log.info("Data successfully exported to: %s", output_path)
        log.info(
            "enecoQ data fetcher completed at %s",
            datetime.datetime.now().isoformat(),
        )

    except click.BadParameter as e:
        _fail(
            log, secrets, "Invalid argument: %s" % e.message,
            EXIT_INVALID_ARGUMENT,
        )
    except exceptions.AuthenticationError as e:
        _fail(log, secrets, "Authentication error: %s" % e, EXIT_AUTH_ERROR)
    except exceptions.FetchError as e:
        _fail(log, secrets, "Fetch error: %s" % e, EXIT_FETCH_ERROR)
    except exceptions.ExportError as e:
        _fail(log, secrets, "Export error: %s" % e, EXIT_EXPORT_ERROR)
    except exceptions.EnecoQError as e:
        _fail(log, secrets, "Error: %s" % e, EXIT_ENECOQ_ERROR)
    except Exception as e:  # pylint: disable=broad-except
        # Last resort, so users get an exit code instead of a traceback.
        _fail(
            log, secrets, "Unexpected error: %s" % e, EXIT_UNEXPECTED_ERROR,
            exc_info=True,
        )


def _load_config(
    config_path: Optional[str],
    log_level: Optional[str],
    log_file: Optional[str],
) -> config_module.Config:
    """Load the configuration for this run.

    Args:
        config_path: Path given with --config, or None to use config.yaml
            in the working directory when it exists.
        log_level: Log level given with --log-level, if any.
        log_file: Log file given with --log-file, if any.

    Returns:
        Loaded configuration.

    Raises:
        click.BadParameter: If the file is missing or invalid.
    """
    if config_path is None and os.path.exists(DEFAULT_CONFIG_PATH):
        config_path = DEFAULT_CONFIG_PATH
    try:
        return config_module.Config.load(
            config_path=config_path, log_level=log_level, log_file=log_file
        )
    except (FileNotFoundError, ValueError) as e:
        raise click.BadParameter(str(e)) from e


def _validate_arguments(
    email: str,
    password: str,
    output_format: str,
    output_path: Optional[str],
) -> None:
    """Validate arguments that Click's option types do not cover.

    Args:
        email: Email address for authentication.
        password: Password for authentication.
        output_format: Output format ("json" or "console").
        output_path: Optional output file path.

    Raises:
        click.BadParameter: If validation fails.
    """
    if "@" not in email:
        raise click.BadParameter("Invalid email address format.")
    if not password:
        raise click.BadParameter("Password cannot be empty.")
    if output_path and output_format.lower() != "json":
        raise click.BadParameter(
            "Output path can only be specified with JSON format."
        )


def _fail(
    log: Optional[logging.Logger],
    secrets: list[str],
    message: str,
    exit_code: int,
    exc_info: bool = False,
) -> NoReturn:
    """Report an error and exit.

    Before logging is set up the logger has no handlers, and Python's
    last-resort handler would print the message a second time, so the
    message is only logged once a logger exists.

    Args:
        log: Configured logger, or None if logging is not set up yet.
        secrets: Values to mask in the message, such as the password.
        message: Error message for the user.
        exit_code: Process exit code.
        exc_info: Whether to log the traceback.
    """
    if log is not None:
        log.error("%s", message, exc_info=exc_info)
    click.echo(logger.mask_secrets(message, secrets), err=True)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
