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
            self._log.error(
                "Failed to fetch today's data: %s", str(e), exc_info=True
            )
            raise exceptions.FetchError(
                "Failed to fetch today's data: %s" % str(e), "FETCH_TODAY_ERROR"
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
            self._log.error(
                "Failed to fetch month's data: %s", str(e), exc_info=True
            )
            raise exceptions.FetchError(
                "Failed to fetch month's data: %s" % str(e), "FETCH_MONTH_ERROR"
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
        # Get iframe containing enecoQ data
        self._log.debug("Locating enecoQ iframe")
        iframe = self._get_enecoq_iframe()
        
        # Select period from dropdown
        self._log.debug("Selecting period: %s", period)
        self._select_period(iframe, period)

        # Wait for data to load
        self._log.debug("Waiting for data to load")
        self.page.wait_for_timeout(2000)  # Wait 2 seconds for data to update

        # Extract data from iframe
        self._log.debug("Extracting power usage data")
        usage_value = self._extract_power_usage(iframe)
        self._log.debug("Power usage: %s kWh", usage_value)
        
        self._log.debug("Extracting power cost data")
        cost_value = self._extract_power_cost(iframe)
        self._log.debug("Power cost: %s JPY", cost_value)
        
        self._log.debug("Extracting CO2 emission data")
        co2_value = self._extract_co2_emission(iframe)
        self._log.debug("CO2 emission: %s kg", co2_value)

        # Create and return PowerData object
        power_data = models.PowerData(
            period=period,
            timestamp=datetime.now(),
            usage=models.PowerUsage(value=usage_value),
            cost=models.PowerCost(value=cost_value),
            co2=models.CO2Emission(value=co2_value),
        )
        
        self._log.info("Successfully fetched %s data", period)
        return power_data

    def _get_enecoq_iframe(self):
        """Get the iframe containing enecoQ data.

        Returns:
            Frame object for the enecoQ iframe.

        Raises:
            FetchError: If iframe is not found.
        """
        try:
            # Wait for iframe to be available
            self.page.wait_for_selector("iframe", timeout=10000)
            
            # Get all iframes
            frames = self.page.frames
            
            # Find the enecoQ iframe (it contains the power data)
            for frame in frames:
                # Check if frame contains enecoQ elements
                if frame.locator("img[alt='使用量']").count() > 0:
                    self._log.debug("Found enecoQ iframe")
                    return frame
            
            # If not found by content, try to get the first non-main iframe
            for frame in frames:
                if frame != self.page.main_frame:
                    self._log.debug("Using first available iframe")
                    return frame
            
            raise exceptions.FetchError(
                "enecoQ iframe not found", "IFRAME_NOT_FOUND"
            )
        except Exception as e:
            self._log.error("Failed to locate iframe: %s", str(e), exc_info=True)
            raise exceptions.FetchError(
                "Failed to locate iframe: %s" % str(e), "IFRAME_ERROR"
            ) from e

    def _select_period(self, iframe, period: str) -> None:
        """Select period from dropdown in iframe.

        Args:
            iframe: Frame object containing the dropdown.
            period: Data period ("today" or "month").

        Raises:
            FetchError: If period selection fails.
        """
        try:
            # Locate period dropdown (combobox)
            combobox = iframe.locator("select").first
            
            if period == "today":
                # Select today option
                self._log.debug("Selecting 'today' option from dropdown")
                combobox.select_option(label="今日")
            elif period == "month":
                # Select month option
                self._log.debug("Selecting 'month' option from dropdown")
                combobox.select_option(label="今月")
            else:
                self._log.error("Invalid period: %s", period)
                raise exceptions.FetchError(
                    "Invalid period: %s" % period, "INVALID_PERIOD"
                )
        except Exception as e:
            self._log.error("Failed to select period: %s", str(e), exc_info=True)
            raise exceptions.FetchError(
                "Failed to select period: %s" % str(e), "PERIOD_SELECT_ERROR"
            ) from e

    def _extract_power_usage(self, iframe) -> float:
        """Extract power usage value from iframe.

        Uses CSS selectors and regex to extract numeric value from the iframe.
        Returns 0.0 if data is not found.

        Args:
            iframe: Frame object containing the data.

        Returns:
            Power usage value in kWh.
        """
        try:
            # Locate dt element containing the usage image
            dt_locator = iframe.locator("dt:has(img[alt='使用量'])")
            
            # Check if element exists
            if dt_locator.count() == 0:
                self._log.warning("Power usage dt element not found")
                return 0.0
            
            # Get the next sibling dd element
            dd_locator = dt_locator.locator("xpath=following-sibling::dd[1]")
            
            if dd_locator.count() == 0:
                self._log.warning("Power usage dd element not found")
                return 0.0

            # Get text content
            text = dd_locator.first.text_content()
            if not text:
                self._log.warning("Power usage text is empty")
                return 0.0

            # Extract numeric value using regex (e.g., "14.50kWh" -> 14.50)
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            if match:
                return float(match.group(1))

            self._log.warning("Could not extract numeric value from: %s", text)
            return 0.0
        except Exception as e:
            # Return empty value if extraction fails
            self._log.warning("Power usage extraction failed: %s", e)
            return 0.0

    def _extract_power_cost(self, iframe) -> float:
        """Extract power cost value from iframe.

        Uses CSS selectors and regex to extract numeric value from the iframe.
        Returns 0.0 if data is not found.

        Args:
            iframe: Frame object containing the data.

        Returns:
            Power cost value in JPY.
        """
        try:
            # Locate dt element containing the cost image
            dt_locator = iframe.locator("dt:has(img[alt='使用料金'])")
            
            # Check if element exists
            if dt_locator.count() == 0:
                self._log.warning("Power cost dt element not found")
                return 0.0
            
            # Get the next sibling dd element
            dd_locator = dt_locator.locator("xpath=following-sibling::dd[1]")
            
            if dd_locator.count() == 0:
                self._log.warning("Power cost dd element not found")
                return 0.0

            # Get text content
            text = dd_locator.first.text_content()
            if not text:
                self._log.warning("Power cost text is empty")
                return 0.0

            # Extract numeric value using regex (e.g., "542.02円" -> 542.02)
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            if match:
                return float(match.group(1))

            self._log.warning("Could not extract numeric value from: %s", text)
            return 0.0
        except Exception as e:
            # Return empty value if extraction fails
            self._log.warning("Power cost extraction failed: %s", e)
            return 0.0

    def _extract_co2_emission(self, iframe) -> float:
        """Extract CO2 emission value from iframe.

        Uses CSS selectors and regex to extract numeric value from the iframe.
        Returns 0.0 if data is not found.

        Args:
            iframe: Frame object containing the data.

        Returns:
            CO2 emission value in kg.
        """
        try:
            # Locate dt element containing the CO2 image
            dt_locator = iframe.locator("dt:has(img[alt='CO2'])")
            
            # Check if element exists
            if dt_locator.count() == 0:
                self._log.warning("CO2 emission dt element not found")
                return 0.0
            
            # Get the next sibling dd element
            dd_locator = dt_locator.locator("xpath=following-sibling::dd[1]")
            
            if dd_locator.count() == 0:
                self._log.warning("CO2 emission dd element not found")
                return 0.0

            # Get text content
            text = dd_locator.first.text_content()
            if not text:
                self._log.warning("CO2 emission text is empty")
                return 0.0

            # Extract numeric value using regex (e.g., "6.53kg" -> 6.53)
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            if match:
                return float(match.group(1))

            self._log.warning("Could not extract numeric value from: %s", text)
            return 0.0
        except Exception as e:
            # Return empty value if extraction fails
            self._log.warning("CO2 emission extraction failed: %s", e)
            return 0.0
