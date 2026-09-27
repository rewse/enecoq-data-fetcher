"""Main controller for enecoQ data fetcher."""

import time
from collections.abc import Callable
from typing import TypeVar

from playwright import sync_api

from enecoq_data_fetcher import (
    authenticator,
    exceptions,
    exporter,
    fetcher,
    logger,
    models,
)
from enecoq_data_fetcher import config as config_module

_T = TypeVar("_T")


class EnecoQController:
    """Runs a fetch: browser lifecycle, login, data retrieval, and export.

    Transient failures are retried by starting over with a new browser.
    """

    DEFAULT_BACKOFF_FACTOR = 2

    def __init__(
        self,
        email: str,
        password: str,
        config: config_module.Config | None = None,
        max_retries: int | None = None,
        backoff_factor: int = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        """Initialize controller with credentials.

        Args:
            email: User's email for enecoQ authentication.
            password: User's password for enecoQ authentication.
            config: Optional configuration. Defaults to Config().
            max_retries: Optional number of retries after the first attempt.
                Overrides config.max_retries.
            backoff_factor: Base of the exponential wait between attempts,
                in seconds.

        Raises:
            ValueError: If max_retries is negative.
        """
        self._config = config or config_module.Config()
        self._max_retries = (
            self._config.max_retries if max_retries is None else max_retries
        )
        if self._max_retries < 0:
            raise ValueError(f"max_retries must be 0 or greater: {self._max_retries}")
        self._backoff_factor = backoff_factor
        self._authenticator = authenticator.EnecoQAuthenticator(email, password)
        self._log = logger.get_logger()

    def fetch_power_data(
        self,
        period: str,
        output_format: str = "json",
        output_path: str | None = None,
    ) -> models.PowerData:
        """Fetch power data for the period and export it.

        Args:
            period: Data period ("today" or "month").
            output_format: Output format ("json" or "console").
            output_path: Optional file path for JSON output.

        Returns:
            PowerData object containing the fetched data.

        Raises:
            AuthenticationError: If the credentials are rejected.
            FetchError: If fetching fails on every attempt.
            ExportError: If exporting fails.
        """
        if period not in ("today", "month"):
            raise exceptions.FetchError(
                f"Invalid period: {period}. Must be 'today' or 'month'.",
                "INVALID_PERIOD",
            )

        self._log.info("Starting data fetch for period: %s", period)
        power_data = self._execute_with_retry(lambda: self._fetch_once(period))
        self._log.info("Data fetch completed successfully")

        self._export_data(power_data, output_format, output_path)
        return power_data

    def _fetch_once(self, period: str) -> models.PowerData:
        """Launch a browser, log in, and fetch the data once.

        Args:
            period: Data period ("today" or "month").

        Returns:
            PowerData object containing the fetched data.

        Raises:
            AuthenticationError: If the credentials are rejected.
            FetchError: If the data cannot be retrieved or parsed.
            playwright.sync_api.Error: If the browser fails.
        """
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(user_agent=self._config.user_agent)
                context.set_default_timeout(self._config.timeout * 1000)
                page = context.new_page()

                self._authenticator.login(page)

                data_fetcher = fetcher.EnecoQDataFetcher(page)
                if period == "today":
                    return data_fetcher.fetch_today_data()
                return data_fetcher.fetch_month_data()
            finally:
                # Closing the browser also closes its contexts and pages.
                browser.close()

    def _execute_with_retry(self, operation: Callable[[], _T]) -> _T:
        """Run the operation, retrying transient failures with backoff.

        FetchError and browser errors are retried. Everything else,
        including AuthenticationError, propagates immediately.

        Args:
            operation: Callable to run.

        Returns:
            Result of the operation.

        Raises:
            FetchError: If every attempt fails with a transient error.
        """
        attempts = self._max_retries + 1
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                return operation()
            except (exceptions.FetchError, sync_api.Error) as e:
                last_error = e
                self._log.warning("Attempt %s/%s failed: %s", attempt, attempts, e)
            if attempt < attempts:
                wait_time = self._backoff_factor**attempt
                self._log.info("Retrying in %s seconds", wait_time)
                time.sleep(wait_time)

        raise exceptions.FetchError(
            f"Operation failed after {attempts} attempts: {last_error}",
            "RETRY_EXHAUSTED",
        ) from last_error

    def _export_data(
        self,
        power_data: models.PowerData,
        output_format: str,
        output_path: str | None,
    ) -> None:
        """Export power data in the given format.

        Args:
            power_data: PowerData object to export.
            output_format: Output format ("json" or "console").
            output_path: Optional file path for JSON output.

        Raises:
            ExportError: If the format is invalid or exporting fails.
        """
        self._log.info("Exporting data in %s format", output_format)
        data_exporter = exporter.DataExporter()
        if output_format == "json":
            data_exporter.export_json(power_data, output_path)
        elif output_format == "console":
            data_exporter.export_console(power_data)
        else:
            raise exceptions.ExportError(
                f"Invalid output format: {output_format}",
                "INVALID_FORMAT",
            )
