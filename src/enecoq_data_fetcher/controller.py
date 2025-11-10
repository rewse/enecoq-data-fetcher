"""Main controller for enecoQ data fetcher."""

import time
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

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
            self._log.error(f"Invalid period specified: {period}")
            raise exceptions.FetchError(
                f"Invalid period: {period}. Must be 'today' or 'month'.",
                "INVALID_PERIOD",
            )

        self._log.info(f"Starting data fetch for period: {period}")

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
                        self._log.debug(f"Fetching {period} data")
                        data_fetcher = fetcher.EnecoQDataFetcher(page)
                        
                        if period == "today":
                            power_data = data_fetcher.fetch_today_data()
                        else:  # period == "month"
                            power_data = data_fetcher.fetch_month_data()
                        
                        self._log.debug(f"Data fetched: usage={power_data.usage.value}, cost={power_data.cost.value}, co2={power_data.co2.value}")
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
                self._log.debug(f"Authentication attempt {attempt}/{self._max_retries}")
                self._authenticator.login(page)
                return  # Success
                
            except exceptions.AuthenticationError as e:
                last_error = e
                self._log.error(f"Authentication failed: {e}")
                
                # Don't retry on authentication errors (invalid credentials)
                # These are not transient failures
                raise
                
            except Exception as e:
                last_error = e
                self._log.warning(f"Authentication attempt {attempt} failed: {e}")
                
                # Retry on other errors (network issues, etc.)
                if attempt < self._max_retries:
                    wait_time = self._backoff_factor ** attempt
                    self._log.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
        
        # All retries exhausted
        raise exceptions.AuthenticationError(
            f"Authentication failed after {self._max_retries} attempts: {last_error}",
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
                self._log.debug(f"Operation attempt {attempt}/{self._max_retries}")
                return operation()
                
            except exceptions.AuthenticationError:
                # Don't retry authentication errors
                self._log.error("Authentication error - not retrying")
                raise
                
            except (exceptions.FetchError, ConnectionError, TimeoutError) as e:
                last_error = e
                self._log.warning(f"Operation attempt {attempt} failed: {e}")
                
                # Retry on transient errors
                if attempt < self._max_retries:
                    wait_time = self._backoff_factor ** attempt
                    self._log.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                    
            except Exception as e:
                # Don't retry on unexpected errors
                self._log.error(f"Unexpected error: {e}", exc_info=True)
                raise
        
        # All retries exhausted
        raise exceptions.FetchError(
            f"Operation failed after {self._max_retries} attempts: {last_error}",
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
        self._log.info(f"Exporting data in {output_format} format")
        data_exporter = exporter.DataExporter()
        
        if output_format == "json":
            data_exporter.export_json(power_data, output_path)
            self._log.debug(f"Data exported to: {output_path or 'stdout'}")
        elif output_format == "console":
            data_exporter.export_console(power_data)
            self._log.debug("Data exported to console")
        else:
            self._log.error(f"Invalid output format: {output_format}")
            raise exceptions.ExportError(
                f"Invalid output format: {output_format}",
                "INVALID_FORMAT",
            )
