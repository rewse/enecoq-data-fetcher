"""Main controller for enecoQ data fetcher."""

import time
from typing import Optional

from playwright.sync_api import sync_playwright

from enecoq_data_fetcher import authenticator
from enecoq_data_fetcher import config as config_module
from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import exporter
from enecoq_data_fetcher import fetcher
from enecoq_data_fetcher import logger
from enecoq_data_fetcher import models


class EnecoQController:
    """Main controller for enecoQ data fetcher.

    Orchestrates authentication, data fetching, and export operations.
    Handles browser lifecycle, error handling, and retry logic.

    Attributes:
        email: User's email for authentication.
        password: User's password for authentication.
        max_retries: Maximum number of retry attempts for operations.
        backoff_factor: Exponential backoff factor for retries.
    """

    # Default configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 2
    DEFAULT_TIMEOUT = 30000  # 30 seconds in milliseconds

    def __init__(
        self,
        email: str,
        password: str,
        config: Optional[config_module.Config] = None,
        max_retries: Optional[int] = None,
        backoff_factor: int = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        """Initialize controller with credentials.

        Args:
            email: User's email for enecoQ authentication.
            password: User's password for enecoQ authentication.
            config: Optional Config object with settings.
            max_retries: Maximum number of retry attempts (overrides config).
            backoff_factor: Exponential backoff factor (default: 2).
        """
        self._email = email
        self._password = password
        self._config = config or config_module.Config()
        self._max_retries = max_retries or self._config.max_retries
        self._backoff_factor = backoff_factor
        self._authenticator = authenticator.EnecoQAuthenticator(
            email, password, user_agent=self._config.user_agent
        )
        self._log = logger.get_logger()

    def fetch_power_data(
        self,
        period: str,
        output_format: str = "json",
        output_path: Optional[str] = None,
    ) -> models.PowerData:
        """Fetch power data for the specified period.

        This is the main entry point for data fetching operations.
        It handles browser lifecycle, authentication, data retrieval,
        and export with automatic retry on transient failures.

        Args:
            period: Data period ("today" or "month").
            output_format: Output format ("json" or "console").
            output_path: Optional file path for JSON output.

        Returns:
            PowerData object containing the fetched data.

        Raises:
            AuthenticationError: If authentication fails after retries.
            FetchError: If data fetching fails after retries.
            ExportError: If data export fails.
        """
        # Validate period
        if period not in ("today", "month"):
            self._log.error("Invalid period specified: %s", period)
            raise exceptions.FetchError(
                "Invalid period: %s. Must be 'today' or 'month'." % period,
                "INVALID_PERIOD",
            )

        self._log.info("Starting data fetch for period: %s", period)

        # Execute with retry logic
        power_data = self._execute_with_retry(
            lambda: self._fetch_data_internal(period)
        )

        self._log.info("Data fetch completed successfully")

        # Export data
        self._export_data(power_data, output_format, output_path)

        return power_data

    def _fetch_data_internal(self, period: str) -> models.PowerData:
        """Internal method to fetch data with browser automation.

        Args:
            period: Data period ("today" or "month").

        Returns:
            PowerData object containing the fetched data.

        Raises:
            AuthenticationError: If authentication fails.
            FetchError: If data fetching fails.
        """
        self._log.debug("Launching browser")
        with sync_playwright() as playwright:
            # Launch browser
            browser = playwright.chromium.launch(headless=True)
            self._log.debug("Browser launched successfully")
            
            try:
                # Create browser context with timeout
                context = browser.new_context()
                timeout_ms = self._config.timeout * 1000  # Convert seconds to milliseconds
                context.set_default_timeout(timeout_ms)
                
                try:
                    # Create new page
                    page = context.new_page()
                    
                    try:
                        # Authenticate
                        self._log.info("Starting authentication")
                        self._authenticate_with_retry(page)
                        self._log.info("Authentication successful")
                        
                        # Fetch data
                        self._log.debug("Fetching %s data", period)
                        data_fetcher = fetcher.EnecoQDataFetcher(page)
                        
                        if period == "today":
                            power_data = data_fetcher.fetch_today_data()
                        else:  # period == "month"
                            power_data = data_fetcher.fetch_month_data()
                        
                        self._log.debug(
                            "Data fetched: usage=%s, cost=%s, co2=%s",
                            power_data.usage.value,
                            power_data.cost.value,
                            power_data.co2.value
                        )
                        return power_data
                        
                    finally:
                        # Close page
                        page.close()
                        
                finally:
                    # Close context
                    context.close()
                    
            finally:
                # Close browser
                browser.close()

    def _authenticate_with_retry(self, page: Page) -> None:
        """Authenticate with retry logic for session expiration.

        Args:
            page: Playwright page object.

        Raises:
            AuthenticationError: If authentication fails after retries.
        """
        last_error = None
        
        for attempt in range(1, self._max_retries + 1):
            try:
                self._log.debug(
                    "Authentication attempt %s/%s", attempt, self._max_retries
                )
                self._authenticator.login(page)
                return  # Success
                
            except exceptions.AuthenticationError as e:
                last_error = e
                self._log.error("Authentication failed: %s", e)
                
                # Don't retry on authentication errors (invalid credentials)
                # These are not transient failures
                raise
                
            except Exception as e:
                last_error = e
                self._log.warning("Authentication attempt %s failed: %s", attempt, e)
                
                # Retry on other errors (network issues, etc.)
                if attempt < self._max_retries:
                    wait_time = self._backoff_factor ** attempt
                    self._log.info("Retrying in %s seconds...", wait_time)
                    time.sleep(wait_time)
                    continue
        
        # All retries exhausted
        raise exceptions.AuthenticationError(
            "Authentication failed after %s attempts: %s" % (
                self._max_retries, last_error
            ),
            "AUTH_RETRY_EXHAUSTED",
        ) from last_error

    def _execute_with_retry(self, operation):
        """Execute operation with exponential backoff retry logic.

        Retries on transient failures like network errors and timeouts.
        Does not retry on authentication errors (invalid credentials).

        Args:
            operation: Callable operation to execute.

        Returns:
            Result of the operation.

        Raises:
            Exception: The last exception if all retries are exhausted.
        """
        last_error = None
        
        for attempt in range(1, self._max_retries + 1):
            try:
                self._log.debug(
                    "Operation attempt %s/%s", attempt, self._max_retries
                )
                return operation()
                
            except exceptions.AuthenticationError:
                # Don't retry authentication errors
                self._log.error("Authentication error - not retrying")
                raise
                
            except (exceptions.FetchError, ConnectionError, TimeoutError) as e:
                last_error = e
                self._log.warning("Operation attempt %s failed: %s", attempt, e)
                
                # Retry on transient errors
                if attempt < self._max_retries:
                    wait_time = self._backoff_factor ** attempt
                    self._log.info("Retrying in %s seconds...", wait_time)
                    time.sleep(wait_time)
                    continue
                    
            except Exception as e:
                # Don't retry on unexpected errors
                self._log.error("Unexpected error: %s", e, exc_info=True)
                raise
        
        # All retries exhausted
        raise exceptions.FetchError(
            "Operation failed after %s attempts: %s" % (
                self._max_retries, last_error
            ),
            "RETRY_EXHAUSTED",
        ) from last_error

    def _export_data(
        self,
        power_data: models.PowerData,
        output_format: str,
        output_path: Optional[str],
    ) -> None:
        """Export power data in specified format.

        Args:
            power_data: PowerData object to export.
            output_format: Output format ("json" or "console").
            output_path: Optional file path for JSON output.

        Raises:
            ExportError: If export fails.
        """
        self._log.info("Exporting data in %s format", output_format)
        data_exporter = exporter.DataExporter()
        
        if output_format == "json":
            data_exporter.export_json(power_data, output_path)
            self._log.debug("Data exported to: %s", output_path or "stdout")
        elif output_format == "console":
            data_exporter.export_console(power_data)
            self._log.debug("Data exported to console")
        else:
            self._log.error("Invalid output format: %s", output_format)
            raise exceptions.ExportError(
                "Invalid output format: %s" % output_format,
                "INVALID_FORMAT",
            )
