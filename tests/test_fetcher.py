"""Tests for data fetcher component."""

from unittest.mock import Mock

from playwright import sync_api

from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import fetcher


def test_fetcher_initialization():
    """Test fetcher initialization."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    assert data_fetcher.page == mock_page
    print("✓ Fetcher initialization test passed")


def _create_mock_iframe_with_data(usage_text, cost_text, co2_text):
    """Helper to create mock iframe with data elements."""
    mock_iframe = Mock()

    def locator_side_effect(selector):
        mock_dt = Mock()
        mock_dd = Mock()

        if "img[alt='使用量']" in selector:
            mock_dt.count.return_value = 1
            mock_dd.count.return_value = 1
            mock_dd.first.text_content.return_value = usage_text
            mock_dt.locator.return_value = mock_dd
            return mock_dt
        elif "img[alt='使用料金']" in selector:
            mock_dt.count.return_value = 1
            mock_dd.count.return_value = 1
            mock_dd.first.text_content.return_value = cost_text
            mock_dt.locator.return_value = mock_dd
            return mock_dt
        elif "img[alt='CO2']" in selector:
            mock_dt.count.return_value = 1
            mock_dd.count.return_value = 1
            mock_dd.first.text_content.return_value = co2_text
            mock_dt.locator.return_value = mock_dd
            return mock_dt
        elif selector == "select":
            mock_select = Mock()
            return mock_select
        return Mock()

    mock_iframe.locator.side_effect = locator_side_effect
    return mock_iframe


def test_extract_power_usage_success():
    """Test successful power usage extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe
    mock_iframe = _create_mock_iframe_with_data("14.50kWh", "0円", "0kg")

    # Extract value
    result = data_fetcher._extract_value(mock_iframe, "使用量")

    assert result == 14.50
    print("✓ Extract power usage success test passed")


def test_extract_power_usage_element_not_found():
    """Test power usage extraction when element not found."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe with element not found
    mock_iframe = Mock()
    mock_dt = Mock()
    mock_dt.count.return_value = 0
    mock_iframe.locator.return_value = mock_dt

    # Missing values are errors, not zero
    try:
        data_fetcher._extract_value(mock_iframe, "使用量")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError:
        pass
    print("✓ Extract power usage element not found test passed")


def test_extract_power_usage_empty_text():
    """Test power usage extraction with empty text."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe with empty text
    mock_iframe = Mock()
    mock_dt = Mock()
    mock_dd = Mock()
    mock_dt.count.return_value = 1
    mock_dd.count.return_value = 1
    mock_dd.first.text_content.return_value = ""
    mock_dt.locator.return_value = mock_dd
    mock_iframe.locator.return_value = mock_dt

    # Missing values are errors, not zero
    try:
        data_fetcher._extract_value(mock_iframe, "使用量")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError:
        pass
    print("✓ Extract power usage empty text test passed")


def test_extract_power_usage_various_formats():
    """Test power usage extraction with various formats."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    test_cases = [
        ("14.50kWh", 14.50),
        ("100kWh", 100.0),
        ("0.5kWh", 0.5),
        ("1234.56 kWh", 1234.56),
        ("1,234.56kWh", 1234.56),
        ("0kWh", 0.0),
    ]

    for text, expected in test_cases:
        mock_iframe = _create_mock_iframe_with_data(text, "0円", "0kg")
        result = data_fetcher._extract_value(mock_iframe, "使用量")
        assert result == expected, f"Failed for {text}"

    print("✓ Extract power usage various formats test passed")


def test_extract_power_cost_success():
    """Test successful power cost extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe
    mock_iframe = _create_mock_iframe_with_data("0kWh", "542.02円", "0kg")

    # Extract value
    result = data_fetcher._extract_value(mock_iframe, "使用料金")

    assert result == 542.02

    # Thousands separators must not truncate the value
    mock_iframe = _create_mock_iframe_with_data("0kWh", "12,345円", "0kg")
    assert data_fetcher._extract_value(mock_iframe, "使用料金") == 12345.0
    print("✓ Extract power cost success test passed")


def test_extract_power_cost_element_not_found():
    """Test power cost extraction when element not found."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe with element not found
    mock_iframe = Mock()
    mock_dt = Mock()
    mock_dt.count.return_value = 0
    mock_iframe.locator.return_value = mock_dt

    # Missing values are errors, not zero
    try:
        data_fetcher._extract_value(mock_iframe, "使用料金")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError:
        pass
    print("✓ Extract power cost element not found test passed")


def test_extract_co2_emission_success():
    """Test successful CO2 emission extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe
    mock_iframe = _create_mock_iframe_with_data("0kWh", "0円", "6.53kg")

    # Extract value
    result = data_fetcher._extract_value(mock_iframe, "CO2")

    assert result == 6.53
    print("✓ Extract CO2 emission success test passed")


def test_extract_co2_emission_element_not_found():
    """Test CO2 emission extraction when element not found."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe with element not found
    mock_iframe = Mock()
    mock_dt = Mock()
    mock_dt.count.return_value = 0
    mock_iframe.locator.return_value = mock_dt

    # Missing values are errors, not zero
    try:
        data_fetcher._extract_value(mock_iframe, "CO2")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError:
        pass
    print("✓ Extract CO2 emission element not found test passed")


def test_select_period_today():
    """Test selecting today period."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe with select element
    mock_iframe = Mock()
    mock_select = Mock()
    mock_select.first = mock_select
    mock_iframe.locator.return_value = mock_select

    # Select period
    data_fetcher._select_period(mock_iframe, "today")

    # Verify select_option was called with correct label
    mock_select.select_option.assert_called_once_with(label="今日")
    print("✓ Select period today test passed")


def test_select_period_month():
    """Test selecting month period."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe with select element
    mock_iframe = Mock()
    mock_select = Mock()
    mock_select.first = mock_select
    mock_iframe.locator.return_value = mock_select

    # Select period
    data_fetcher._select_period(mock_iframe, "month")

    # Verify select_option was called with correct label
    mock_select.select_option.assert_called_once_with(label="今月")
    print("✓ Select period month test passed")


def test_select_period_invalid():
    """Test selecting invalid period."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe
    mock_iframe = Mock()
    mock_select = Mock()
    mock_select.first = mock_select
    mock_iframe.locator.return_value = mock_select

    # Try to select invalid period
    try:
        data_fetcher._select_period(mock_iframe, "invalid")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Invalid period" in str(e)

    print("✓ Select period invalid test passed")


def test_select_period_error():
    """Test period selection with error."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Create mock iframe that raises error
    mock_iframe = Mock()
    mock_select = Mock()
    mock_select.first = mock_select
    mock_select.select_option.side_effect = sync_api.Error("Selector error")
    mock_iframe.locator.return_value = mock_select

    # Try to select period
    try:
        data_fetcher._select_period(mock_iframe, "today")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Failed to select period" in str(e)

    print("✓ Select period error test passed")


def test_fetch_today_data_error():
    """Test today data fetch with error."""
    mock_page = Mock()
    mock_page.wait_for_selector.side_effect = sync_api.Error("Network error")
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Try to fetch data
    try:
        data_fetcher.fetch_today_data()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Failed to fetch today's data" in str(e)

    print("✓ Fetch today data error test passed")


def test_fetch_month_data_error():
    """Test month data fetch with error."""
    mock_page = Mock()
    mock_page.wait_for_selector.side_effect = sync_api.Error("Network error")
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    # Try to fetch data
    try:
        data_fetcher.fetch_month_data()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Failed to fetch month's data" in str(e)

    print("✓ Fetch month data error test passed")


def _create_mock_frame(url, has_data_marker):
    """Helper to create a mock frame.

    Args:
        url: URL of the frame.
        has_data_marker: Whether the frame contains the enecoQ data marker.

    Returns:
        Mock frame object.
    """
    mock_frame = Mock()
    mock_frame.url = url

    def locator_side_effect(selector):
        mock_locator = Mock()
        if "img[alt='使用量']" in selector:
            mock_locator.count.return_value = 1 if has_data_marker else 0
        else:
            mock_locator.count.return_value = 0
        return mock_locator

    mock_frame.locator.side_effect = locator_side_effect
    return mock_frame


def test_get_enecoq_iframe_found_by_data_marker():
    """Test iframe lookup returns the frame holding enecoQ data."""
    mock_page = Mock()
    weather_frame = _create_mock_frame(
        "https://ap.otenki.com/index.php", has_data_marker=False
    )
    enecoq_frame = _create_mock_frame(
        "https://ses.me-eco.jp/mini/", has_data_marker=True
    )
    mock_page.frames = [
        Mock(url="https://www.cyberhome.ne.jp/"),
        weather_frame,
        enecoq_frame,
    ]
    mock_page.frames[0].locator.side_effect = lambda selector: Mock(
        count=Mock(return_value=0)
    )
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    result = data_fetcher._get_enecoq_iframe()

    assert result is enecoq_frame
    print("✓ Get enecoQ iframe found by data marker test passed")


def test_get_enecoq_iframe_no_fallback_to_unrelated_frame():
    """Test iframe lookup never falls back to an unrelated frame.

    The enecoQ widget is unavailable for a while after the month rollover.
    Other iframes on the page (e.g. the weather widget) hold unrelated select
    elements, so returning one of them makes the period selection hang until
    it times out. An unavailable widget must fail fast instead.
    """
    mock_page = Mock()
    weather_frame = _create_mock_frame(
        "https://ap.otenki.com/index.php", has_data_marker=False
    )
    mock_page.frames = [Mock(url="https://www.cyberhome.ne.jp/"), weather_frame]
    mock_page.frames[0].locator.side_effect = lambda selector: Mock(
        count=Mock(return_value=0)
    )
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    try:
        data_fetcher._get_enecoq_iframe()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert e.error_code == "IFRAME_NOT_FOUND", (
            f"Unexpected error code: {e.error_code}"
        )

    print("✓ Get enecoQ iframe no fallback to unrelated frame test passed")


def test_get_enecoq_iframe_waits_for_late_rendering():
    """Test iframe lookup waits for the widget to finish rendering."""
    mock_page = Mock()
    enecoq_frame = _create_mock_frame(
        "https://ses.me-eco.jp/mini/", has_data_marker=False
    )
    mock_page.frames = [enecoq_frame]

    # Render the data marker only after the first poll
    def render_on_wait(_timeout):
        enecoq_frame.locator.side_effect = lambda selector: Mock(
            count=Mock(return_value=1)
        )

    mock_page.wait_for_timeout.side_effect = render_on_wait
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    result = data_fetcher._get_enecoq_iframe()

    assert result is enecoq_frame
    assert mock_page.wait_for_timeout.called
    print("✓ Get enecoQ iframe waits for late rendering test passed")


def test_fetch_month_data_success():
    """Test a full month fetch with separators and a local timestamp."""
    mock_page = Mock()
    mock_iframe = _create_mock_iframe_with_data("1,234.5kWh", "12,345円", "6.53kg")
    mock_page.frames = [mock_iframe]
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    data = data_fetcher.fetch_month_data()

    assert data.period == "month"
    assert data.usage.value == 1234.5
    assert data.cost.value == 12345.0
    assert data.co2.value == 6.53
    assert data.timestamp.utcoffset() is not None
    assert "+" in data.to_dict()["timestamp"] or "-" in data.to_dict()["timestamp"][19:]
    print("✓ Fetch month data success test passed")


def test_fetch_month_data_placeholder_value():
    """Test that a placeholder instead of a number fails the fetch."""
    mock_page = Mock()
    mock_iframe = _create_mock_iframe_with_data("--kWh", "0円", "0kg")
    mock_page.frames = [mock_iframe]
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    try:
        data_fetcher.fetch_month_data()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Failed to fetch month's data" in str(e)
        assert "power usage" in str(e)
    print("✓ Fetch month data placeholder value test passed")


def test_fetch_today_data_missing_value():
    """Test that a missing value fails the fetch instead of returning 0."""
    mock_page = Mock()
    mock_iframe = _create_mock_iframe_with_data("1kWh", "2円", "3kg")
    base_locator = mock_iframe.locator.side_effect

    def locator_without_co2(selector):
        if "img[alt='CO2']" in selector:
            return Mock(count=Mock(return_value=0))
        return base_locator(selector)

    mock_iframe.locator.side_effect = locator_without_co2
    mock_page.frames = [mock_iframe]
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)

    try:
        data_fetcher.fetch_today_data()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert e.error_code == "FETCH_TODAY_ERROR"
        assert "CO2 emission" in str(e)
    print("✓ Fetch today data missing value test passed")


if __name__ == "__main__":
    print("Running fetcher tests...\n")

    test_fetcher_initialization()
    test_extract_power_usage_success()
    test_extract_power_usage_element_not_found()
    test_extract_power_usage_empty_text()
    test_extract_power_usage_various_formats()
    test_extract_power_cost_success()
    test_extract_power_cost_element_not_found()
    test_extract_co2_emission_success()
    test_extract_co2_emission_element_not_found()
    test_select_period_today()
    test_select_period_month()
    test_select_period_invalid()
    test_select_period_error()
    test_fetch_today_data_error()
    test_fetch_month_data_error()
    test_get_enecoq_iframe_found_by_data_marker()
    test_get_enecoq_iframe_no_fallback_to_unrelated_frame()
    test_get_enecoq_iframe_waits_for_late_rendering()
    test_fetch_month_data_success()
    test_fetch_month_data_placeholder_value()
    test_fetch_today_data_missing_value()

    print("\n✓ All fetcher tests passed!")
