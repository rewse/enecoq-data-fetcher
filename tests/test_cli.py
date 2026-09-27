"""Tests for CLI functionality."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import Mock
from unittest.mock import patch

from click.testing import CliRunner

from enecoq_data_fetcher import cli
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import models

# The fetcher records aware local time, and enecoQ users are in Japan.
JST = timezone(timedelta(hours=9))


def test_cli_help():
    """Test CLI help message."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])

    assert result.exit_code == 0
    assert "enecoQ Data Fetcher" in result.output
    assert "--email" in result.output
    assert "--password" in result.output
    assert "--period" in result.output
    assert "--format" in result.output
    assert "--config" in result.output
    print("✓ CLI help message works")


def test_cli_missing_required_args():
    """Test CLI with missing required arguments."""
    runner = CliRunner()

    # Missing email and password
    result = runner.invoke(cli.main, [])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()
    print("✓ CLI validates required arguments")


def test_cli_invalid_email():
    """Test CLI with invalid email format."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main, ["--email", "invalid-email", "--password", "test123"]
    )

    # Debug: print exit code and output
    if result.exit_code != 6:
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

    assert result.exit_code == 6
    assert "Invalid argument" in result.output
    assert "email" in result.output.lower()
    print("✓ CLI validates email format")


def test_cli_invalid_period():
    """Test CLI with invalid period."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--email", "test@example.com", "--password", "test123", "--period", "invalid"],
    )

    assert result.exit_code != 0
    assert "Invalid value" in result.output or "period" in result.output.lower()
    print("✓ CLI validates period argument")


def test_cli_invalid_format():
    """Test CLI with invalid format."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--email", "test@example.com", "--password", "test123", "--format", "invalid"],
    )

    assert result.exit_code != 0
    assert "Invalid value" in result.output or "format" in result.output.lower()
    print("✓ CLI validates format argument")


def test_cli_output_with_console_format():
    """Test CLI rejects output path with console format."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--email",
            "test@example.com",
            "--password",
            "test123",
            "--format",
            "console",
            "--output",
            "output.json",
        ],
    )

    assert result.exit_code == 6
    assert "Invalid argument" in result.output
    print("✓ CLI validates output path with format")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_success_console_format(mock_controller_class):
    """Test successful CLI execution with console format."""
    # Create mock controller instance
    mock_controller = Mock()
    mock_controller_class.return_value = mock_controller

    # Create mock power data
    mock_data = models.PowerData(
        period="today",
        timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=JST),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )
    mock_controller.fetch_power_data.return_value = mock_data

    # Run CLI
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--email",
            "test@example.com",
            "--password",
            "test123",
            "--period",
            "today",
            "--format",
            "console",
        ],
    )

    assert result.exit_code == 0
    mock_controller.fetch_power_data.assert_called_once_with(
        period="today",
        output_format="console",
        output_path=None,
    )
    print("✓ CLI executes successfully with console format")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_success_json_format(mock_controller_class):
    """Test successful CLI execution with JSON format."""
    # Create mock controller instance
    mock_controller = Mock()
    mock_controller_class.return_value = mock_controller

    # Create mock power data
    mock_data = models.PowerData(
        period="month",
        timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=JST),
        usage=models.PowerUsage(value=450.0),
        cost=models.PowerCost(value=12500.0),
        co2=models.CO2Emission(value=225.0),
    )
    mock_controller.fetch_power_data.return_value = mock_data

    # Run CLI with output file
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "test123",
                "--period",
                "month",
                "--format",
                "json",
                "--output",
                "output.json",
            ],
        )

        assert result.exit_code == 0
        assert "successfully exported" in result.output
        mock_controller.fetch_power_data.assert_called_once_with(
            period="month",
            output_format="json",
            output_path="output.json",
        )
    print("✓ CLI executes successfully with JSON format")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_authentication_error(mock_controller_class):
    """Test CLI handles authentication errors."""
    # Create mock controller that raises AuthenticationError
    mock_controller = Mock()
    mock_controller_class.return_value = mock_controller
    mock_controller.fetch_power_data.side_effect = exceptions.AuthenticationError(
        "Invalid credentials"
    )

    # Run CLI
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--email", "test@example.com", "--password", "wrong", "--format", "console"],
    )

    assert result.exit_code == 1
    assert "Authentication error" in result.output
    print("✓ CLI handles authentication errors")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_fetch_error(mock_controller_class):
    """Test CLI handles fetch errors."""
    # Create mock controller that raises FetchError
    mock_controller = Mock()
    mock_controller_class.return_value = mock_controller
    mock_controller.fetch_power_data.side_effect = exceptions.FetchError(
        "Network error"
    )

    # Run CLI
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--email", "test@example.com", "--password", "test123", "--format", "console"],
    )

    assert result.exit_code == 2
    assert "Fetch error" in result.output
    print("✓ CLI handles fetch errors")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_export_error(mock_controller_class):
    """Test CLI handles export errors."""
    # Create mock controller that raises ExportError
    mock_controller = Mock()
    mock_controller_class.return_value = mock_controller
    mock_controller.fetch_power_data.side_effect = exceptions.ExportError(
        "File write error"
    )

    # Run CLI
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--email", "test@example.com", "--password", "test123", "--format", "json"],
    )

    assert result.exit_code == 3
    assert "Export error" in result.output
    print("✓ CLI handles export errors")


def test_cli_with_custom_config():
    """Test CLI with custom config file path."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])

    # Check that --config option is available
    assert result.exit_code == 0
    assert "--config" in result.output
    assert "config.yaml" in result.output
    print("✓ CLI accepts custom config file path")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_with_config_parameter(mock_controller_class):
    """Test CLI execution with config parameter."""
    # Create mock controller instance
    mock_controller = Mock()
    mock_controller_class.return_value = mock_controller

    # Create mock power data
    mock_data = models.PowerData(
        period="today",
        timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=JST),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )
    mock_controller.fetch_power_data.return_value = mock_data

    # Run CLI with custom config
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("custom_config.yaml", "w", encoding="utf-8") as f:
            f.write("timeout: 60\n")
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "test123",
                "--config",
                "custom_config.yaml",
                "--format",
                "console",
            ],
        )

    assert result.exit_code == 0, result.output
    config_arg = mock_controller_class.call_args.kwargs["config"]
    assert config_arg.timeout == 60
    print("✓ CLI executes with custom config parameter")


def test_cli_missing_explicit_config():
    """Test that a missing --config file is reported instead of ignored."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "test123",
                "--config",
                "missing.yaml",
            ],
        )

    assert result.exit_code == 6
    assert "Config file not found" in result.output
    print("✓ CLI reports missing explicit config file")


def _sample_today_data():
    """Return PowerData for a successful today fetch."""
    return models.PowerData(
        period="today",
        timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=JST),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )


def test_cli_invalid_config_content():
    """Test that an invalid config file exits with the argument error code."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("bad.yaml", "w", encoding="utf-8") as f:
            f.write("timeout: thirty\n")
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "test123",
                "--config",
                "bad.yaml",
            ],
        )

    assert result.exit_code == 6, result.output
    assert "timeout" in result.output
    print("✓ CLI rejects invalid config content")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_loads_default_config_when_present(mock_controller_class):
    """Test that config.yaml in the working directory is loaded by default."""
    mock_controller_class.return_value.fetch_power_data.return_value = (
        _sample_today_data()
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("config.yaml", "w", encoding="utf-8") as f:
            f.write("timeout: 90\n")
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "test123",
                "--format",
                "console",
            ],
        )

    assert result.exit_code == 0, result.output
    assert mock_controller_class.call_args.kwargs["config"].timeout == 90
    print("✓ CLI loads config.yaml by default")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_uses_defaults_without_config(mock_controller_class):
    """Test that a missing default config.yaml is not an error."""
    mock_controller_class.return_value.fetch_power_data.return_value = (
        _sample_today_data()
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "test123",
                "--format",
                "console",
            ],
        )

    assert result.exit_code == 0, result.output
    assert mock_controller_class.call_args.kwargs["config"].timeout == 30
    print("✓ CLI uses defaults without config.yaml")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_masks_password_in_log_file(mock_controller_class):
    """Test that the password never reaches the log file."""
    mock_controller_class.return_value.fetch_power_data.side_effect = (
        exceptions.FetchError("Page echoed hunter2-secret back")
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "hunter2-secret",
                "--log-file",
                "run.log",
            ],
        )
        with open("run.log", encoding="utf-8") as f:
            content = f.read()

    assert result.exit_code == 2, result.output
    assert "hunter2-secret" not in content
    assert "Page echoed **** back" in content
    print("✓ CLI masks password in log file")


def test_cli_reports_argument_error_once():
    """Test that an error before logging is set up is shown once."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--email",
            "invalid-email",
            "--password",
            "test123",
        ],
    )

    assert result.exit_code == 6
    assert result.output.count("Invalid argument") == 1, result.output
    print("✓ CLI reports argument error once")


@patch("enecoq_data_fetcher.cli.controller.EnecoQController")
def test_cli_masks_password_in_error_output(mock_controller_class):
    """Test that the password never reaches the error message on stderr."""
    mock_controller_class.return_value.fetch_power_data.side_effect = RuntimeError(
        "Page echoed hunter2-secret back"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "--email",
                "test@example.com",
                "--password",
                "hunter2-secret",
                "--log-file",
                "run.log",
            ],
        )
        with open("run.log", encoding="utf-8") as f:
            content = f.read()

    assert result.exit_code == 5, result.output
    assert "hunter2-secret" not in result.output, result.output
    assert "Unexpected error: Page echoed **** back" in result.output
    assert "hunter2-secret" not in content, content
    print("✓ CLI masks password in error output")


if __name__ == "__main__":
    test_cli_help()
    test_cli_missing_required_args()
    test_cli_invalid_email()
    test_cli_invalid_period()
    test_cli_invalid_format()
    test_cli_output_with_console_format()
    test_cli_success_console_format()
    test_cli_success_json_format()
    test_cli_authentication_error()
    test_cli_fetch_error()
    test_cli_export_error()
    test_cli_with_custom_config()
    test_cli_with_config_parameter()
    test_cli_missing_explicit_config()
    test_cli_invalid_config_content()
    test_cli_loads_default_config_when_present()
    test_cli_uses_defaults_without_config()
    test_cli_masks_password_in_log_file()
    test_cli_reports_argument_error_once()
    test_cli_masks_password_in_error_output()
    print("\nAll CLI tests passed!")
