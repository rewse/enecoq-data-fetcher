"""Tests for data models."""

from datetime import datetime

from enecoq_data_fetcher import models


def test_power_usage_creation():
    """Test PowerUsage model creation."""
    usage = models.PowerUsage(value=12.5)
    
    assert usage.value == 12.5
    assert usage.unit == "kWh"
    print("✓ PowerUsage creation test passed")


def test_power_usage_to_dict():
    """Test PowerUsage to_dict conversion."""
    usage = models.PowerUsage(value=12.5)
    result = usage.to_dict()
    
    assert result == 12.5
    assert isinstance(result, float)
    print("✓ PowerUsage to_dict test passed")


def test_power_cost_creation():
    """Test PowerCost model creation."""
    cost = models.PowerCost(value=350.0)
    
    assert cost.value == 350.0
    assert cost.unit == "JPY"
    print("✓ PowerCost creation test passed")


def test_power_cost_to_dict():
    """Test PowerCost to_dict conversion."""
    cost = models.PowerCost(value=350.0)
    result = cost.to_dict()
    
    assert result == 350.0
    assert isinstance(result, float)
    print("✓ PowerCost to_dict test passed")


def test_co2_emission_creation():
    """Test CO2Emission model creation."""
    co2 = models.CO2Emission(value=6.25)
    
    assert co2.value == 6.25
    assert co2.unit == "kg"
    print("✓ CO2Emission creation test passed")


def test_co2_emission_to_dict():
    """Test CO2Emission to_dict conversion."""
    co2 = models.CO2Emission(value=6.25)
    result = co2.to_dict()
    
    assert result == 6.25
    assert isinstance(result, float)
    print("✓ CO2Emission to_dict test passed")


def test_power_data_creation():
    """Test PowerData model creation."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    power_data = models.PowerData(
        period="today",
        timestamp=timestamp,
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )
    
    assert power_data.period == "today"
    assert power_data.timestamp == timestamp
    assert power_data.usage.value == 12.5
    assert power_data.cost.value == 350.0
    assert power_data.co2.value == 6.25
    print("✓ PowerData creation test passed")


def test_power_data_to_dict():
    """Test PowerData to_dict conversion."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    power_data = models.PowerData(
        period="today",
        timestamp=timestamp,
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )
    
    result = power_data.to_dict()
    
    assert result["period"] == "today"
    assert result["timestamp"] == "2024-01-15T10:30:00"
    assert result["usage"] == 12.5
    assert result["cost"] == 350.0
    assert result["co2"] == 6.25
    print("✓ PowerData to_dict test passed")


def test_power_data_with_month_period():
    """Test PowerData with month period."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    power_data = models.PowerData(
        period="month",
        timestamp=timestamp,
        usage=models.PowerUsage(value=450.0),
        cost=models.PowerCost(value=12500.0),
        co2=models.CO2Emission(value=225.0),
    )
    
    result = power_data.to_dict()
    
    assert result["period"] == "month"
    assert result["usage"] == 450.0
    assert result["cost"] == 12500.0
    assert result["co2"] == 225.0
    print("✓ PowerData with month period test passed")


def test_custom_units():
    """Test models with custom units."""
    usage = models.PowerUsage(value=100.0, unit="MWh")
    cost = models.PowerCost(value=1000.0, unit="USD")
    co2 = models.CO2Emission(value=50.0, unit="ton")
    
    assert usage.unit == "MWh"
    assert cost.unit == "USD"
    assert co2.unit == "ton"
    
    # to_dict should still return numeric values
    assert usage.to_dict() == 100.0
    assert cost.to_dict() == 1000.0
    assert co2.to_dict() == 50.0
    print("✓ Custom units test passed")


def test_zero_values():
    """Test models with zero values."""
    power_data = models.PowerData(
        period="today",
        timestamp=datetime.now(),
        usage=models.PowerUsage(value=0.0),
        cost=models.PowerCost(value=0.0),
        co2=models.CO2Emission(value=0.0),
    )
    
    result = power_data.to_dict()
    
    assert result["usage"] == 0.0
    assert result["cost"] == 0.0
    assert result["co2"] == 0.0
    print("✓ Zero values test passed")


def test_large_values():
    """Test models with large values."""
    power_data = models.PowerData(
        period="month",
        timestamp=datetime.now(),
        usage=models.PowerUsage(value=9999.99),
        cost=models.PowerCost(value=999999.99),
        co2=models.CO2Emission(value=4999.99),
    )
    
    result = power_data.to_dict()
    
    assert result["usage"] == 9999.99
    assert result["cost"] == 999999.99
    assert result["co2"] == 4999.99
    print("✓ Large values test passed")


if __name__ == "__main__":
    print("Running model tests...\n")
    
    test_power_usage_creation()
    test_power_usage_to_dict()
    test_power_cost_creation()
    test_power_cost_to_dict()
    test_co2_emission_creation()
    test_co2_emission_to_dict()
    test_power_data_creation()
    test_power_data_to_dict()
    test_power_data_with_month_period()
    test_custom_units()
    test_zero_values()
    test_large_values()
    
    print("\n✓ All model tests passed!")
