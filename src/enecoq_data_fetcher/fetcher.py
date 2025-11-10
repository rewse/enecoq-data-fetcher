"""Data fetcher component for enecoQ web service."""

import re
from datetime import datetime

from playwright.sync_api import Page

from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import logger
from enecoq_data_fetcher import models


class EnecoQDataFetcher:
    """Fetches and parses power data from enecoQ web service.

    This class handles data retrieval from the enecoQ web interface using
    Playwright for browser automation. It extracts power usage, cost, and
    CO2 emission data from the web page.

    Attributes:
        page: Playwright page object for browser interaction.
    """

    def __init__(self, page: Page) -> None:
        """Initialize fetcher with Playwright page.

        Args:
            page: Playwright page object for browser interaction.
        """
        self.page = page
        self._log = logger.get_logger()

    def fetch_today_data(self) -> models.PowerData:
        """Fetch and parse today's power data.

        Navigates to the enecoQ data page, selects "today" period,
        and extracts power usage, cost, and CO2 emission data.

        Returns:
            PowerData object containing today's data.

        Raises:
            FetchError: If data retrieval or parsing fails.
        """
        try:
            self._log.info("Fetching today's data")
            return self._fetch_data_for_period("today")
        except Exception as e:
            self._log.error(f"Failed to fetch today's data: {str(e)}", exc_info=True)
            raise exceptions.FetchError(
                f"Failed to fetch today's data: {str(e)}", "FETCH_TODAY_ERROR"
            ) from e

    def fetch_month_data(self) -> models.PowerData:
        """Fetch and parse this month's power data.

        Navigates to the enecoQ data page, selects "month" period,
        and extracts power usage, cost, and CO2 emission data.

        Returns:
            PowerData object containing this month's data.

        Raises:
            FetchError: If data retrieval or parsing fails.
        """
        try:
            self._log.info("Fetching month's data")
            return self._fetch_data_for_period("month")
        except Exception as e:
            self._log.error(f"Failed to fetch month's data: {str(e)}", exc_info=True)
            raise exceptions.FetchError(
                f"Failed to fetch month's data: {str(e)}", "FETCH_MONTH_ERROR"
            ) from e

    def _fetch_data_for_period(self, period: str) -> models.PowerData:
        """Fetch data for specified period.

        Args:
            period: Data period ("today" or "month").

        Returns:
            PowerData object containing the requested data.

        Raises:
            FetchError: If data retrieval or parsing fails.
        """
        # Select period from dropdown
        self._log.debug(f"Selecting period: {period}")
        self._select_period(period)

        # Wait for page to load data
        self._log.debug("Waiting for page to load data")
        self.page.wait_for_load_state("networkidle")

        # Extract data from page
        self._log.debug("Extracting power usage data")
        usage_value = self._extract_power_usage()
        self._log.debug(f"Power usage: {usage_value} kWh")
        
        self._log.debug("Extracting power cost data")
        cost_value = self._extract_power_cost()
        self._log.debug(f"Power cost: {cost_value} JPY")
        
        self._log.debug("Extracting CO2 emission data")
        co2_value = self._extract_co2_emission()
        self._log.debug(f"CO2 emission: {co2_value} kg")

        # Create and return PowerData object
        power_data = models.PowerData(
            period=period,
            timestamp=datetime.now(),
            usage=models.PowerUsage(value=usage_value),
            cost=models.PowerCost(value=cost_value),
            co2=models.CO2Emission(value=co2_value),
        )
        
        self._log.info(f"Successfully fetched {period} data")
        return power_data

    def _select_period(self, period: str) -> None:
        """Select period from dropdown.

        Args:
            period: Data period ("today" or "month").

        Raises:
            FetchError: If period selection fails.
        """
        try:
            # Locate period dropdown selector
            selector = 'select[name="dtm"]'
            
            if period == "today":
                # Select today option (value="daily")
                self._log.debug("Selecting 'daily' option from dropdown")
                self.page.select_option(selector, value="daily")
            elif period == "month":
                # Select month option (value="monthly")
                self._log.debug("Selecting 'monthly' option from dropdown")
                self.page.select_option(selector, value="monthly")
            else:
                self._log.error(f"Invalid period: {period}")
                raise exceptions.FetchError(
                    f"Invalid period: {period}", "INVALID_PERIOD"
                )
        except Exception as e:
            self._log.error(f"Failed to select period: {str(e)}", exc_info=True)
            raise exceptions.FetchError(
                f"Failed to select period: {str(e)}", "PERIOD_SELECT_ERROR"
            ) from e

    def _extract_power_usage(self) -> float:
        """Extract power usage value from page.

        Uses CSS selectors and regex to extract numeric value from the page.
        Returns 0.0 if data is not found.

        Returns:
            Power usage value in kWh.
        """
        try:
            # Locate power usage element by ID
            locator = self.page.locator('#usage')

            # Check if element exists
            if locator.count() == 0:
                self._log.warning("Power usage element not found")
                return 0.0

            # Get text content
            text = locator.first.text_content()
            if not text:
                self._log.warning("Power usage text is empty")
                return 0.0

            # Extract numeric value using regex (e.g., "14.50kWh" -> 14.50)
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            if match:
                return float(match.group(1))

            self._log.warning(f"Could not extract numeric value from: {text}")
            return 0.0
        except Exception as e:
            # Return empty value if extraction fails
            self._log.warning(f"Power usage extraction failed: {e}")
            return 0.0

    def _extract_power_cost(self) -> float:
        """Extract power cost value from page.

        Uses CSS selectors and regex to extract numeric value from the page.
        Returns 0.0 if data is not found.

        Returns:
            Power cost value in JPY.
        """
        try:
            # Locate power cost element by ID
            locator = self.page.locator('#yen')

            # Check if element exists
            if locator.count() == 0:
                self._log.warning("Power cost element not found")
                return 0.0

            # Get text content
            text = locator.first.text_content()
            if not text:
                self._log.warning("Power cost text is empty")
                return 0.0

            # Extract numeric value using regex (e.g., "542.02円" -> 542.02)
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            if match:
                return float(match.group(1))

            self._log.warning(f"Could not extract numeric value from: {text}")
            return 0.0
        except Exception as e:
            # Return empty value if extraction fails
            self._log.warning(f"Power cost extraction failed: {e}")
            return 0.0

    def _extract_co2_emission(self) -> float:
        """Extract CO2 emission value from page.

        Uses CSS selectors and regex to extract numeric value from the page.
        Returns 0.0 if data is not found.

        Returns:
            CO2 emission value in kg.
        """
        try:
            # Locate CO2 emission element by ID
            locator = self.page.locator('#co2')

            # Check if element exists
            if locator.count() == 0:
                self._log.warning("CO2 emission element not found")
                return 0.0

            # Get text content
            text = locator.first.text_content()
            if not text:
                self._log.warning("CO2 emission text is empty")
                return 0.0

            # Extract numeric value using regex (e.g., "6.53kg" -> 6.53)
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            if match:
                return float(match.group(1))

            self._log.warning(f"Could not extract numeric value from: {text}")
            return 0.0
        except Exception as e:
            # Return empty value if extraction fails
            self._log.warning(f"CO2 emission extraction failed: {e}")
            return 0.0
