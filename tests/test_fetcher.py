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


def test_extract_power_usage_success():
    """Test successful power usage extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locator
    mock_locator = Mock()
    mock_locator.count.return_value = 1
    mock_locator.first.text_content.return_value = "14.50kWh"
    mock_page.locator.return_value = mock_locator
    
    # Extract value
    result = data_fetcher._extract_power_usage()
    
    assert result == 14.50
    print("✓ Extract power usage success test passed")


def test_extract_power_usage_element_not_found():
    """Test power usage extraction when element not found."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locator - element not found
    mock_locator = Mock()
    mock_locator.count.return_value = 0
    mock_page.locator.return_value = mock_locator
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_power_usage()
    
    assert result == 0.0
    print("✓ Extract power usage element not found test passed")


def test_extract_power_usage_empty_text():
    """Test power usage extraction with empty text."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locator - empty text
    mock_locator = Mock()
    mock_locator.count.return_value = 1
    mock_locator.first.text_content.return_value = ""
    mock_page.locator.return_value = mock_locator
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_power_usage()
    
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
        mock_locator = Mock()
        mock_locator.count.return_value = 1
        mock_locator.first.text_content.return_value = text
        mock_page.locator.return_value = mock_locator
        
        result = data_fetcher._extract_power_usage()
        assert result == expected, f"Failed for {text}"
    
    print("✓ Extract power usage various formats test passed")


def test_extract_power_cost_success():
    """Test successful power cost extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locator
    mock_locator = Mock()
    mock_locator.count.return_value = 1
    mock_locator.first.text_content.return_value = "542.02円"
    mock_page.locator.return_value = mock_locator
    
    # Extract value
    result = data_fetcher._extract_power_cost()
    
    assert result == 542.02
    print("✓ Extract power cost success test passed")


def test_extract_power_cost_element_not_found():
    """Test power cost extraction when element not found."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locator - element not found
    mock_locator = Mock()
    mock_locator.count.return_value = 0
    mock_page.locator.return_value = mock_locator
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_power_cost()
    
    assert result == 0.0
    print("✓ Extract power cost element not found test passed")


def test_extract_co2_emission_success():
    """Test successful CO2 emission extraction."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locator
    mock_locator = Mock()
    mock_locator.count.return_value = 1
    mock_locator.first.text_content.return_value = "6.53kg"
    mock_page.locator.return_value = mock_locator
    
    # Extract value
    result = data_fetcher._extract_co2_emission()
    
    assert result == 6.53
    print("✓ Extract CO2 emission success test passed")


def test_extract_co2_emission_element_not_found():
    """Test CO2 emission extraction when element not found."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locator - element not found
    mock_locator = Mock()
    mock_locator.count.return_value = 0
    mock_page.locator.return_value = mock_locator
    
    # Extract value - should return 0.0
    result = data_fetcher._extract_co2_emission()
    
    assert result == 0.0
    print("✓ Extract CO2 emission element not found test passed")


def test_select_period_today():
    """Test selecting today period."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Select period
    data_fetcher._select_period("today")
    
    # Verify select_option was called with correct value
    mock_page.select_option.assert_called_once_with('select[name="dtm"]', value="daily")
    print("✓ Select period today test passed")


def test_select_period_month():
    """Test selecting month period."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Select period
    data_fetcher._select_period("month")
    
    # Verify select_option was called with correct value
    mock_page.select_option.assert_called_once_with('select[name="dtm"]', value="monthly")
    print("✓ Select period month test passed")


def test_select_period_invalid():
    """Test selecting invalid period."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Try to select invalid period
    try:
        data_fetcher._select_period("invalid")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Invalid period" in str(e)
    
    print("✓ Select period invalid test passed")


def test_select_period_error():
    """Test period selection with error."""
    mock_page = Mock()
    mock_page.select_option.side_effect = Exception("Selector error")
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Try to select period
    try:
        data_fetcher._select_period("today")
        assert False, "Should have raised FetchError"
    except exceptions.FetchError as e:
        assert "Failed to select period" in str(e)
    
    print("✓ Select period error test passed")


def test_fetch_today_data_success():
    """Test successful today data fetch."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locators for data extraction
    def locator_side_effect(selector):
        mock_locator = Mock()
        mock_locator.count.return_value = 1
        if selector == '#usage':
            mock_locator.first.text_content.return_value = "12.5kWh"
        elif selector == '#yen':
            mock_locator.first.text_content.return_value = "350.0円"
        elif selector == '#co2':
            mock_locator.first.text_content.return_value = "6.25kg"
        return mock_locator
    
    mock_page.locator.side_effect = locator_side_effect
    
    # Fetch data
    result = data_fetcher.fetch_today_data()
    
    # Verify result
    assert isinstance(result, models.PowerData)
    assert result.period == "today"
    assert result.usage.value == 12.5
    assert result.cost.value == 350.0
    assert result.co2.value == 6.25
    
    print("✓ Fetch today data success test passed")


def test_fetch_month_data_success():
    """Test successful month data fetch."""
    mock_page = Mock()
    data_fetcher = fetcher.EnecoQDataFetcher(mock_page)
    
    # Setup mock locators for data extraction
    def locator_side_effect(selector):
        mock_locator = Mock()
        mock_locator.count.return_value = 1
        if selector == '#usage':
            mock_locator.first.text_content.return_value = "450.0kWh"
        elif selector == '#yen':
            mock_locator.first.text_content.return_value = "12500.0円"
        elif selector == '#co2':
            mock_locator.first.text_content.return_value = "225.0kg"
        return mock_locator
    
    mock_page.locator.side_effect = locator_side_effect
    
    # Fetch data
    result = data_fetcher.fetch_month_data()
    
    # Verify result
    assert isinstance(result, models.PowerData)
    assert result.period == "month"
    assert result.usage.value == 450.0
    assert result.cost.value == 12500.0
    assert result.co2.value == 225.0
    
    print("✓ Fetch month data success test passed")


def test_fetch_today_data_error():
    """Test today data fetch with error."""
    mock_page = Mock()
    mock_page.select_option.side_effect = Exception("Network error")
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
    mock_page.select_option.side_effect = Exception("Network error")
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
    test_fetch_today_data_success()
    test_fetch_month_data_success()
    test_fetch_today_data_error()
    test_fetch_month_data_error()
    
    print("\n✓ All fetcher tests passed!")
