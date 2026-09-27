"""Data fetcher component for enecoQ web service."""

import datetime
import re
from typing import ClassVar

from playwright import sync_api

from enecoq_data_fetcher import exceptions, logger, models


class EnecoQDataFetcher:
    """Fetches and parses power data from the enecoQ widget.

    Attributes:
        page: Playwright page showing the logged-in CYBERHOME portal.
    """

    # Element the enecoQ widget renders once its data is available
    DATA_MARKER_SELECTOR = "img[alt='使用量']"

    # Time budget for the enecoQ iframe to render its data
    IFRAME_TIMEOUT_MS = 10000
    IFRAME_POLL_INTERVAL_MS = 500

    # Time for the widget to refresh its values after the period changes
    DATA_UPDATE_WAIT_MS = 2000

    # Labels of the period options in the widget's dropdown
    PERIOD_LABELS: ClassVar[dict[str, str]] = {"today": "今日", "month": "今月"}

    # English names for the alt text of each value's image, used in messages
    VALUE_NAMES: ClassVar[dict[str, str]] = {
        "CO2": "CO2 emission",
        "使用料金": "power cost",
        "使用量": "power usage",
    }

    # Values may carry thousands separators, such as "12,345円".
    _NUMBER_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?")

    def __init__(self, page: sync_api.Page) -> None:
        """Initialize fetcher with Playwright page.

        Args:
            page: Playwright page showing the logged-in portal.
        """
        self.page = page
        self._log = logger.get_logger()

    def fetch_today_data(self) -> models.PowerData:
        """Fetch today's power data.

        Returns:
            PowerData object containing today's data.

        Raises:
            FetchError: If the data cannot be retrieved or parsed.
        """
        return self._fetch_data_for_period("today")

    def fetch_month_data(self) -> models.PowerData:
        """Fetch this month's power data.

        Returns:
            PowerData object containing this month's data.

        Raises:
            FetchError: If the data cannot be retrieved or parsed.
        """
        return self._fetch_data_for_period("month")

    def _fetch_data_for_period(self, period: str) -> models.PowerData:
        """Select the period in the widget and read its values.

        Args:
            period: Data period ("today" or "month").

        Returns:
            PowerData object containing the requested data.

        Raises:
            FetchError: If the data cannot be retrieved or parsed.
        """
        self._log.info("Fetching %s data", period)
        try:
            iframe = self._get_enecoq_iframe()
            self._select_period(iframe, period)
            self.page.wait_for_timeout(self.DATA_UPDATE_WAIT_MS)
            power_data = models.PowerData(
                period=period,
                timestamp=datetime.datetime.now().astimezone(),
                usage=models.PowerUsage(value=self._extract_value(iframe, "使用量")),
                cost=models.PowerCost(value=self._extract_value(iframe, "使用料金")),
                co2=models.CO2Emission(value=self._extract_value(iframe, "CO2")),
            )
        except (exceptions.FetchError, sync_api.Error) as e:
            self._log.error("Failed to fetch %s's data: %s", period, e)
            raise exceptions.FetchError(
                f"Failed to fetch {period}'s data: {e}",
                f"FETCH_{period.upper()}_ERROR",
            ) from e
        self._log.info("Successfully fetched %s data", period)
        return power_data

    def _get_enecoq_iframe(self) -> sync_api.Frame:
        """Get the iframe containing the enecoQ widget.

        The widget is identified by the data marker it renders. Other iframes
        on the page hold unrelated select elements, so they are never used as
        a substitute.

        Returns:
            Frame object for the enecoQ widget.

        Raises:
            FetchError: If the widget does not render in time.
        """
        try:
            self.page.wait_for_selector("iframe", timeout=self.IFRAME_TIMEOUT_MS)

            # The widget may still be rendering, so poll for the data marker.
            waited_ms = 0
            while True:
                for frame in self.page.frames:
                    if frame.locator(self.DATA_MARKER_SELECTOR).count() > 0:
                        self._log.debug("Found enecoQ iframe: %s", frame.url)
                        return frame
                if waited_ms >= self.IFRAME_TIMEOUT_MS:
                    break
                self.page.wait_for_timeout(self.IFRAME_POLL_INTERVAL_MS)
                waited_ms += self.IFRAME_POLL_INTERVAL_MS
        except sync_api.Error as e:
            raise exceptions.FetchError(
                f"Failed to locate iframe: {e}", "IFRAME_ERROR"
            ) from e

        # The widget is unavailable for a while after the month rollover.
        # Fail fast so the caller gets an accurate reason instead of a period
        # selection timeout on an unrelated iframe.
        raise exceptions.FetchError(
            "enecoQ iframe not found: no iframe rendered "
            f"{self.DATA_MARKER_SELECTOR} within {self.IFRAME_TIMEOUT_MS}ms",
            "IFRAME_NOT_FOUND",
        )

    def _select_period(self, iframe: sync_api.Frame, period: str) -> None:
        """Select the period in the widget's dropdown.

        Args:
            iframe: Frame containing the widget.
            period: Data period ("today" or "month").

        Raises:
            FetchError: If the period is invalid or cannot be selected.
        """
        label = self.PERIOD_LABELS.get(period)
        if label is None:
            raise exceptions.FetchError(f"Invalid period: {period}", "INVALID_PERIOD")
        self._log.debug("Selecting period: %s", period)
        try:
            iframe.locator("select").first.select_option(label=label)
        except sync_api.Error as e:
            raise exceptions.FetchError(
                f"Failed to select period: {e}", "PERIOD_SELECT_ERROR"
            ) from e

    def _extract_value(self, iframe: sync_api.Frame, alt: str) -> float:
        """Read the number shown next to the widget image with the alt text.

        Args:
            iframe: Frame containing the widget.
            alt: Alt text of the image that labels the value, such as "使用量".

        Returns:
            The value without its unit.

        Raises:
            FetchError: If the value is missing or is not a number.
        """
        name = self.VALUE_NAMES.get(alt, alt)
        dt_locator = iframe.locator(f"dt:has(img[alt='{alt}'])")
        dd_locator = dt_locator.locator("xpath=following-sibling::dd[1]")
        if dt_locator.count() == 0 or dd_locator.count() == 0:
            raise exceptions.FetchError(
                f"Value for {name} not found", "VALUE_NOT_FOUND"
            )

        text = dd_locator.first.text_content() or ""
        match = self._NUMBER_PATTERN.search(text)
        if match is None:
            raise exceptions.FetchError(
                f"Could not parse {name} from {text!r}",
                "VALUE_PARSE_ERROR",
            )
        value = float(match.group(0).replace(",", ""))
        self._log.debug("Extracted %s: %s", name, value)
        return value
