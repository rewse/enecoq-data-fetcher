"""Command-line interface for enecoQ data fetcher."""

import sys
from typing import Optional

import click

from enecoq_data_fetcher import controller
from enecoq_data_fetcher import exceptions


@click.command()
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
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level (default: INFO).",
)
def main(
    email: str,
    password: str,
    period: str,
    output_format: str,
    output_path: Optional[str],
    log_level: str,
) -> int:
    """enecoQ Data Fetcher - Fetch power usage data from enecoQ Web Service.

    This tool retrieves power usage, cost, and CO2 emission data from the
    enecoQ Web Service.

    Examples:

        \b
        # Fetch this month's data and display in console
        $ enecoq-fetch --email user@example.com --password secret --format console

        \b
        # Fetch today's data and save to JSON file
        $ enecoq-fetch --email user@example.com --password secret --period today --output data.json

        \b
        # Fetch with debug logging
        $ enecoq-fetch --email user@example.com --password secret --log-level DEBUG
    """
    try:
        # Validate arguments
        _validate_arguments(email, password, period, output_format, output_path)

        # TODO: Configure logging based on log_level
        # This will be implemented in task 9

        # Create controller
        enecoq_controller = controller.EnecoQController(email, password)

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
            else:
                # Data was already printed by exporter
                pass

    except click.BadParameter as e:
        click.echo(f"Invalid argument: {e.message}", err=True)
        sys.exit(6)

    except exceptions.AuthenticationError as e:
        click.echo(f"Authentication error: {e}", err=True)
        sys.exit(1)

    except exceptions.FetchError as e:
        click.echo(f"Fetch error: {e}", err=True)
        sys.exit(2)

    except exceptions.ExportError as e:
        click.echo(f"Export error: {e}", err=True)
        sys.exit(3)

    except exceptions.EnecoQError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(4)

    except Exception as e:
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
