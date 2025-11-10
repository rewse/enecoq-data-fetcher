"""Tests for CLI functionality."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from enecoq_data_fetcher import cli
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import models
from datetime import datetime


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
    result = runner.invoke(cli.main, [
        "--email", "invalid-email",
        "--password", "test123"
    ])
    
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
    result = runner.invoke(cli.main, [
        "--email", "test@example.com",
        "--password", "test123",
        "--period", "invalid"
    ])
    
    assert result.exit_code != 0
    assert "Invalid value" in result.output or "period" in result.output.lower()
    print("✓ CLI validates period argument")


def test_cli_invalid_format():
    """Test CLI with invalid format."""
    runner = CliRunner()
    result = runner.invoke(cli.main, [
        "--email", "test@example.com",
        "--password", "test123",
        "--format", "invalid"
    ])
    
    assert result.exit_code != 0
    assert "Invalid value" in result.output or "format" in result.output.lower()
    print("✓ CLI validates format argument")


def test_cli_output_with_console_format():
    """Test CLI rejects output path with console format."""
    runner = CliRunner()
    result = runner.invoke(cli.main, [
        "--email", "test@example.com",
        "--password", "test123",
        "--format", "console",
        "--output", "output.json"
    ])
    
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
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )
    mock_controller.fetch_power_data.return_value = mock_data
    
    # Run CLI
    runner = CliRunner()
    result = runner.invoke(cli.main, [
        "--email", "test@example.com",
        "--password", "test123",
        "--period", "today",
        "--format", "console"
    ])
    
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
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=450.0),
        cost=models.PowerCost(value=12500.0),
        co2=models.CO2Emission(value=225.0),
    )
    mock_controller.fetch_power_data.return_value = mock_data
    
    # Run CLI with output file
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli.main, [
            "--email", "test@example.com",
            "--password", "test123",
            "--period", "month",
            "--format", "json",
            "--output", "output.json"
        ])
        
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
    result = runner.invoke(cli.main, [
        "--email", "test@example.com",
        "--password", "wrong",
        "--format", "console"
    ])
    
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
    result = runner.invoke(cli.main, [
        "--email", "test@example.com",
        "--password", "test123",
        "--format", "console"
    ])
    
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
    result = runner.invoke(cli.main, [
        "--email", "test@example.com",
        "--password", "test123",
        "--format", "json"
    ])
    
    assert result.exit_code == 3
    assert "Export error" in result.output
    print("✓ CLI handles export errors")


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
    print("\nAll CLI tests passed!")
