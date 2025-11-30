"""Tests for data fetcher component."""

from datetime import datetime
from unittest.mock import Mock

from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import fetcher
from enecoq_data_fetcher import models


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
    result = data_fetcher._extract_power_usage(mock_iframe)
    
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
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_power_usage(mock_iframe)
    
    assert result == 0.0
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
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_power_usage(mock_iframe)
    
    assert result == 0.0
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
    ]
    
    for text, expected in test_cases:
        mock_iframe = _create_mock_iframe_with_data(text, "0円", "0kg")
        result = data_fetcher._extract_power_usage(mock_iframe)
        assert result == expected, "Failed for %s" % text
    
    print("✓ Extract power usage various formats test passed")


def test_extract_power_cost_success():
    """Test successful power cost extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Create mock iframe
    mock_iframe = _create_mock_iframe_with_data("0kWh", "542.02円", "0kg")
    
    # Extract value
    result = data_fetcher._extract_power_cost(mock_iframe)
    
    assert result == 542.02
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
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_power_cost(mock_iframe)
    
    assert result == 0.0
    print("✓ Extract power cost element not found test passed")


def test_extract_co2_emission_success():
    """Test successful CO2 emission extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Create mock iframe
    mock_iframe = _create_mock_iframe_with_data("0kWh", "0円", "6.53kg")
    
    # Extract value
    result = data_fetcher._extract_co2_emission(mock_iframe)
    
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
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_co2_emission(mock_iframe)
    
    assert result == 0.0
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
    mock_select.select_option.side_effect = Exception("Selector error")
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
    mock_page.wait_for_selector.side_effect = Exception("Network error")
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
    mock_page.wait_for_selector.side_effect = Exception("Network error")
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Try to fetch data
    try:
        data_fetcher.fetch_month_data()
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Failed to fetch month's data" in str(e)
    
    print("✓ Fetch month data error test passed")


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
    
    print("\n✓ All fetcher tests passed!")
