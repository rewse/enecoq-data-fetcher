"""Integration tests for enecoQ data fetcher.

This module contains end-to-end integration tests that verify
the complete workflow of the application.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from playwright import sync_api

from enecoq_data_fetcher import cli
from enecoq_data_fetcher import config
from enecoq_data_fetcher import controller
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import models
from click.testing import CliRunner


def test_end_to_end_json_output():
    """Test complete workflow with JSON output to file."""
    print("\n=== Testing end-to-end JSON output ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        # Setup mock browser automation
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock successful authentication and data fetch
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data"
            ) as mock_fetch:
                # Setup mock data
                mock_data = models.PowerData(
                    period="month",
                    timestamp=datetime(2024, 1, 15, 10, 30, 0),
                    usage=models.PowerUsage(value=450.0),
                    cost=models.PowerCost(value=12500.0),
                    co2=models.CO2Emission(value=225.0),
                )
                mock_fetch.return_value = mock_data

                # Run CLI
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

                    # Verify CLI execution
                    assert result.exit_code == 0, f"CLI failed: {result.output}"
                    assert "successfully exported" in result.output

                    # Verify output file
                    assert os.path.exists("output.json")
                    with open("output.json", "r") as f:
                        data = json.load(f)

                    assert data["period"] == "month"
                    assert data["usage"] == 450.0
                    assert data["cost"] == 12500.0
                    assert data["co2"] == 225.0

                    print("✓ End-to-end JSON output test passed")


def test_end_to_end_console_output():
    """Test complete workflow with console output."""
    print("\n=== Testing end-to-end console output ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        # Setup mock browser automation
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock successful authentication and data fetch
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_today_data"
            ) as mock_fetch:
                # Setup mock data
                mock_data = models.PowerData(
                    period="today",
                    timestamp=datetime(2024, 1, 15, 10, 30, 0),
                    usage=models.PowerUsage(value=12.5),
                    cost=models.PowerCost(value=350.0),
                    co2=models.CO2Emission(value=6.25),
                )
                mock_fetch.return_value = mock_data

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

                # Verify CLI execution
                assert result.exit_code == 0, f"CLI failed: {result.output}"
                assert "Power Usage" in result.output
                assert "12.5" in result.output
                assert "350.0" in result.output
                assert "6.25" in result.output

                print("✓ End-to-end console output test passed")


def test_controller_with_config():
    """Test controller initialization with configuration."""
    print("\n=== Testing controller with config ===")

    # Create custom config
    cfg = config.Config(
        log_level="DEBUG",
        timeout=60,
        max_retries=5,
    )

    # Create controller
    ctl = controller.EnecoQController(
        email="test@example.com",
        password="test123",
        config=cfg,
    )

    # Verify configuration
    assert ctl._config.log_level == "DEBUG"
    assert ctl._config.timeout == 60
    assert ctl._max_retries == 5

    print("✓ Controller with config test passed")


def test_error_handling_authentication():
    """Test error handling for authentication failures."""
    print("\n=== Testing authentication error handling ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        # Setup mock browser automation
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock authentication failure
        with patch(
            "enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"
        ) as mock_login:
            mock_login.side_effect = exceptions.AuthenticationError(
                "Invalid credentials"
            )

            # Run CLI
            runner = CliRunner()
            result = runner.invoke(
                cli.main,
                [
                    "--email",
                    "test@example.com",
                    "--password",
                    "wrong",
                    "--format",
                    "console",
                ],
            )

            # Verify error handling
            assert result.exit_code == 1
            assert "Authentication error" in result.output

            print("✓ Authentication error handling test passed")


def test_error_handling_fetch():
    """Test error handling for fetch failures."""
    print("\n=== Testing fetch error handling ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        # Setup mock browser automation
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock successful authentication but fetch failure
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data"
            ) as mock_fetch:
                mock_fetch.side_effect = exceptions.FetchError("Network error")

                # Run CLI
                runner = CliRunner()
                with patch("time.sleep"):  # Skip actual sleep
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

                # Verify error handling
                assert result.exit_code == 2
                assert "Fetch error" in result.output

                print("✓ Fetch error handling test passed")


def test_config_file_integration():
    """Test configuration file loading integration."""
    print("\n=== Testing config file integration ===")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write("""
log_level: DEBUG
timeout: 60
max_retries: 5
""")
        temp_path = f.name

    try:
        with patch(
            "enecoq_data_fetcher.controller.sync_api.sync_playwright"
        ) as mock_playwright:
            # Setup mock browser automation
            mock_browser = Mock()
            mock_context = Mock()
            mock_page = Mock()

            mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            # Mock successful authentication and data fetch
            with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
                with patch(
                    "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_today_data"
                ) as mock_fetch:
                    mock_data = models.PowerData(
                        period="today",
                        timestamp=datetime(2024, 1, 15, 10, 30, 0),
                        usage=models.PowerUsage(value=12.5),
                        cost=models.PowerCost(value=350.0),
                        co2=models.CO2Emission(value=6.25),
                    )
                    mock_fetch.return_value = mock_data

                    # Run CLI with config file
                    runner = CliRunner()
                    result = runner.invoke(
                        cli.main,
                        [
                            "--email",
                            "test@example.com",
                            "--password",
                            "test123",
                            "--config",
                            temp_path,
                            "--period",
                            "today",
                            "--format",
                            "console",
                        ],
                    )

                    # Verify CLI execution
                    assert result.exit_code == 0, f"CLI failed: {result.output}"

                    print("✓ Config file integration test passed")
    finally:
        os.unlink(temp_path)


def test_retry_mechanism():
    """Test retry mechanism for transient failures."""
    print("\n=== Testing retry mechanism ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        # Setup mock browser automation
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock authentication success
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data"
            ) as mock_fetch:
                # First call fails, second succeeds
                mock_data = models.PowerData(
                    period="month",
                    timestamp=datetime(2024, 1, 15, 10, 30, 0),
                    usage=models.PowerUsage(value=450.0),
                    cost=models.PowerCost(value=12500.0),
                    co2=models.CO2Emission(value=225.0),
                )
                mock_fetch.side_effect = [
                    exceptions.FetchError("Temporary error"),
                    mock_data,
                ]

                # Create controller with retry
                cfg = config.Config(max_retries=3)
                ctl = controller.EnecoQController(
                    email="test@example.com",
                    password="test123",
                    config=cfg,
                )

                # Fetch data (should succeed on retry)
                with patch("time.sleep"):  # Skip actual sleep
                    result = ctl.fetch_power_data(
                        period="month", output_format="console"
                    )

                # Verify success
                assert result.usage.value == 450.0
                assert mock_fetch.call_count == 2  # First failed, second succeeded

                print("✓ Retry mechanism test passed")


def _mock_browser(mock_playwright):
    """Wire a mocked sync_playwright to return a mock browser.

    Args:
        mock_playwright: Patched sync_playwright.

    Returns:
        Tuple of the mock browser, context, and page.
    """
    mock_browser = Mock()
    mock_context = Mock()
    mock_page = Mock()
    launcher = mock_playwright.return_value.__enter__.return_value.chromium
    launcher.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    return mock_browser, mock_context, mock_page


def _sample_month_data():
    """Return PowerData for a successful month fetch."""
    return models.PowerData(
        period="month",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=450.0),
        cost=models.PowerCost(value=12500.0),
        co2=models.CO2Emission(value=225.0),
    )


def test_retry_on_login_timeout():
    """Test that a browser timeout during login is retried."""
    print("\n=== Testing retry on login timeout ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        mock_browser, _, _ = _mock_browser(mock_playwright)
        with patch(
            "enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"
        ) as mock_login:
            mock_login.side_effect = [
                sync_api.TimeoutError("Timeout 30000ms exceeded"),
                None,
            ]
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data"
            ) as mock_fetch:
                mock_fetch.return_value = _sample_month_data()
                ctl = controller.EnecoQController(
                    "test@example.com", "test123", config=config.Config()
                )
                with patch("time.sleep"):
                    result = ctl.fetch_power_data("month", "console")

    assert result.usage.value == 450.0
    assert mock_login.call_count == 2
    assert mock_browser.close.call_count == 2
    print("✓ Retry on login timeout test passed")


def test_no_retry_on_authentication_error():
    """Test that rejected credentials are not retried."""
    print("\n=== Testing no retry on authentication error ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        mock_browser, _, _ = _mock_browser(mock_playwright)
        with patch(
            "enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"
        ) as mock_login:
            mock_login.side_effect = exceptions.AuthenticationError("Rejected")
            ctl = controller.EnecoQController(
                "test@example.com", "wrong", config=config.Config()
            )
            try:
                with patch("time.sleep") as mock_sleep:
                    ctl.fetch_power_data("month", "console")
                assert False, "Should have raised AuthenticationError"
            except exceptions.AuthenticationError:
                pass

    assert mock_login.call_count == 1
    assert not mock_sleep.called
    assert mock_browser.close.call_count == 1
    print("✓ No retry on authentication error test passed")


def test_retries_are_added_to_first_attempt():
    """Test that max_retries counts retries after the first attempt."""
    print("\n=== Testing retry count ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data"
            ) as mock_fetch:
                mock_fetch.side_effect = exceptions.FetchError("Widget down")
                ctl = controller.EnecoQController(
                    "test@example.com",
                    "test123",
                    config=config.Config(max_retries=2),
                )
                try:
                    with patch("time.sleep") as mock_sleep:
                        ctl.fetch_power_data("month", "console")
                    assert False, "Should have raised FetchError"
                except exceptions.FetchError as e:
                    assert e.error_code == "RETRY_EXHAUSTED"

    assert mock_fetch.call_count == 3
    assert [c.args[0] for c in mock_sleep.call_args_list] == [2, 4]
    print("✓ Retry count test passed")


def test_zero_retries_tries_once():
    """Test that max_retries of 0 still makes one attempt."""
    print("\n=== Testing zero retries ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data"
            ) as mock_fetch:
                mock_fetch.return_value = _sample_month_data()
                ctl = controller.EnecoQController(
                    "test@example.com",
                    "test123",
                    config=config.Config(max_retries=0),
                )
                result = ctl.fetch_power_data("month", "console")

    assert result.cost.value == 12500.0
    assert mock_fetch.call_count == 1
    print("✓ Zero retries test passed")


def test_browser_context_uses_config():
    """Test that user_agent and timeout from the config reach the browser."""
    print("\n=== Testing browser context settings ===")

    with patch(
        "enecoq_data_fetcher.controller.sync_api.sync_playwright"
    ) as mock_playwright:
        mock_browser, mock_context, _ = _mock_browser(mock_playwright)
        with patch("enecoq_data_fetcher.authenticator.EnecoQAuthenticator.login"):
            with patch(
                "enecoq_data_fetcher.fetcher.EnecoQDataFetcher.fetch_month_data"
            ) as mock_fetch:
                mock_fetch.return_value = _sample_month_data()
                ctl = controller.EnecoQController(
                    "test@example.com",
                    "test123",
                    config=config.Config(user_agent="TestAgent/1.0", timeout=45),
                )
                ctl.fetch_power_data("month", "console")

    mock_browser.new_context.assert_called_once_with(user_agent="TestAgent/1.0")
    mock_context.set_default_timeout.assert_called_once_with(45000)
    print("✓ Browser context settings test passed")


def test_data_model_serialization():
    """Test data model serialization for export."""
    print("\n=== Testing data model serialization ===")

    # Create power data
    power_data = models.PowerData(
        period="today",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )

    # Convert to dict
    data_dict = power_data.to_dict()

    # Verify structure
    assert data_dict["period"] == "today"
    assert data_dict["timestamp"] == "2024-01-15T10:30:00"
    assert data_dict["usage"] == 12.5
    assert data_dict["cost"] == 350.0
    assert data_dict["co2"] == 6.25

    # Verify JSON serialization
    json_str = json.dumps(data_dict)
    assert json_str is not None

    # Verify deserialization
    loaded_dict = json.loads(json_str)
    assert loaded_dict["usage"] == 12.5

    print("✓ Data model serialization test passed")


if __name__ == "__main__":
    print("Running integration tests...")

    test_end_to_end_json_output()
    test_end_to_end_console_output()
    test_controller_with_config()
    test_error_handling_authentication()
    test_error_handling_fetch()
    test_config_file_integration()
    test_retry_mechanism()
    test_retry_on_login_timeout()
    test_no_retry_on_authentication_error()
    test_retries_are_added_to_first_attempt()
    test_zero_retries_tries_once()
    test_browser_context_uses_config()
    test_data_model_serialization()

    print("\n" + "=" * 50)
    print("✓ All integration tests passed!")
    print("=" * 50)
