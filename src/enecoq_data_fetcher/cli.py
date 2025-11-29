"""Command-line interface for enecoQ data fetcher."""

import os
import sys
from typing import Optional

import click

from enecoq_data_fetcher import __version__
from enecoq_data_fetcher import config as config_module
from enecoq_data_fetcher import controller
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import logger


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
    type=click.Path(exists=False),
    default="config.yaml",
    help="Configuration file path (default: config.yaml).",
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
    config_path: str,
    log_level: str,
    log_file: Optional[str],
) -> int:
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
    try:
        # Validate arguments
        _validate_arguments(email, password, period, output_format, output_path)

        # Load configuration
        config = config_module.Config.load(
            config_path=config_path if config_path != "config.yaml" or os.path.exists(config_path) else None,
            log_level=log_level.upper() if log_level is not None else None,
        )

        # Override log_file from command line if specified
        if log_file is not None:
            config.log_file = log_file

        # Configure logging
        log = logger.setup_logger(log_level=config.log_level, log_file=config.log_file)
        log.info("Starting enecoQ data fetcher")
        log.debug(f"Parameters - Period: {period}, Format: {output_format}, Config: {config_path}")
        log.debug(f"Configuration - Log level: {config.log_level}, Timeout: {config.timeout}, Max retries: {config.max_retries}")

        # Create controller with config
        enecoq_controller = controller.EnecoQController(email, password, config=config)

        # Fetch power data
        power_data = enecoq_controller.fetch_power_data(
            period=period.lower(),
            output_format=output_format.lower(),
            output_path=output_path,
        )

        # Display success message for JSON format
        if output_format.lower() == "json":
            if output_path:
                click.echo(f"Data successfully exported to: {output_path}")
                log.info(f"Data successfully exported to: {output_path}")
            else:
                # Data was already printed by exporter
                log.info("Data successfully exported to console")
        
        log.info("enecoQ data fetcher completed successfully")

    except click.BadParameter as e:
        log = logger.get_logger()
        log.error(f"Invalid argument: {e.message}")
        click.echo(f"Invalid argument: {e.message}", err=True)
        sys.exit(6)

    except exceptions.AuthenticationError as e:
        log = logger.get_logger()
        log.error(f"Authentication error: {e}")
        click.echo(f"Authentication error: {e}", err=True)
        sys.exit(1)

    except exceptions.FetchError as e:
        log = logger.get_logger()
        log.error(f"Fetch error: {e}")
        click.echo(f"Fetch error: {e}", err=True)
        sys.exit(2)

    except exceptions.ExportError as e:
        log = logger.get_logger()
        log.error(f"Export error: {e}")
        click.echo(f"Export error: {e}", err=True)
        sys.exit(3)

    except exceptions.EnecoQError as e:
        log = logger.get_logger()
        log.error(f"Error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(4)

    except Exception as e:
        log = logger.get_logger()
        log.error(f"Unexpected error: {e}", exc_info=True)
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(5)


def _validate_arguments(
    email: str,
    password: str,
    period: str,
    output_format: str,
    output_path: Optional[str],
) -> None:
    """Validate command-line arguments.

    Args:
        email: Email address for authentication.
        password: Password for authentication.
        period: Data period ("today" or "month").
        output_format: Output format ("json" or "console").
        output_path: Optional output file path.

    Raises:
        click.BadParameter: If validation fails.
    """
    # Validate email format (basic check)
    if not email or "@" not in email:
        raise click.BadParameter("Invalid email address format.")

    # Validate password (not empty)
    if not password:
        raise click.BadParameter("Password cannot be empty.")

    # Validate period (already validated by Click's Choice type)
    # Additional validation if needed
    if period.lower() not in ("today", "month"):
        raise click.BadParameter(
            f"Invalid period: {period}. Must be 'today' or 'month'."
        )

    # Validate output format (already validated by Click's Choice type)
    if output_format.lower() not in ("json", "console"):
        raise click.BadParameter(
            f"Invalid format: {output_format}. Must be 'json' or 'console'."
        )

    # Validate output_path is only used with JSON format
    if output_path and output_format.lower() != "json":
        raise click.BadParameter(
            "Output path can only be specified with JSON format."
        )


if __name__ == "__main__":
    sys.exit(main())
