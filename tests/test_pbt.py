"""Property-based tests for enecoQ data fetcher.

This module contains property-based tests using Hypothesis to verify
invariants and properties of the data models and components.
"""

from datetime import datetime

from hypothesis import given, assume, settings
from hypothesis import strategies as st

from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import models


# Custom strategies for domain-specific types
positive_floats = st.floats(min_value=0.0, max_value=1e9, allow_nan=False)
period_strategy = st.sampled_from(["today", "month"])
unit_strategy = st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


# =============================================================================
# PowerUsage Properties
# =============================================================================

@given(value=positive_floats)
def test_power_usage_value_preserved(value):
    """Property: PowerUsage preserves the input value."""
    usage = models.PowerUsage(value=value)
    assert usage.value == value


@given(value=positive_floats)
def test_power_usage_to_dict_returns_value(value):
    """Property: PowerUsage.to_dict() returns the numeric value."""
    usage = models.PowerUsage(value=value)
    assert usage.to_dict() == value


@given(value=positive_floats, unit=unit_strategy)
def test_power_usage_custom_unit_preserved(value, unit):
    """Property: PowerUsage preserves custom unit."""
    usage = models.PowerUsage(value=value, unit=unit)
    assert usage.unit == unit
    # to_dict should still return only the value
    assert usage.to_dict() == value


# =============================================================================
# PowerCost Properties
# =============================================================================

@given(value=positive_floats)
def test_power_cost_value_preserved(value):
    """Property: PowerCost preserves the input value."""
    cost = models.PowerCost(value=value)
    assert cost.value == value


@given(value=positive_floats)
def test_power_cost_to_dict_returns_value(value):
    """Property: PowerCost.to_dict() returns the numeric value."""
    cost = models.PowerCost(value=value)
    assert cost.to_dict() == value


@given(value=positive_floats, unit=unit_strategy)
def test_power_cost_custom_unit_preserved(value, unit):
    """Property: PowerCost preserves custom unit."""
    cost = models.PowerCost(value=value, unit=unit)
    assert cost.unit == unit
    assert cost.to_dict() == value


# =============================================================================
# CO2Emission Properties
# =============================================================================

@given(value=positive_floats)
def test_co2_emission_value_preserved(value):
    """Property: CO2Emission preserves the input value."""
    co2 = models.CO2Emission(value=value)
    assert co2.value == value


@given(value=positive_floats)
def test_co2_emission_to_dict_returns_value(value):
    """Property: CO2Emission.to_dict() returns the numeric value."""
    co2 = models.CO2Emission(value=value)
    assert co2.to_dict() == value


# =============================================================================
# PowerData Properties
# =============================================================================

@given(
    period=period_strategy,
    usage_value=positive_floats,
    cost_value=positive_floats,
    co2_value=positive_floats,
)
def test_power_data_preserves_all_values(period, usage_value, cost_value, co2_value):
    """Property: PowerData preserves all input values."""
    timestamp = datetime.now()
    power_data = models.PowerData(
        period=period,
        timestamp=timestamp,
        usage=models.PowerUsage(value=usage_value),
        cost=models.PowerCost(value=cost_value),
        co2=models.CO2Emission(value=co2_value),
    )
    
    assert power_data.period == period
    assert power_data.timestamp == timestamp
    assert power_data.usage.value == usage_value
    assert power_data.cost.value == cost_value
    assert power_data.co2.value == co2_value


@given(
    period=period_strategy,
    usage_value=positive_floats,
    cost_value=positive_floats,
    co2_value=positive_floats,
)
def test_power_data_to_dict_structure(period, usage_value, cost_value, co2_value):
    """Property: PowerData.to_dict() returns correct structure."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    power_data = models.PowerData(
        period=period,
        timestamp=timestamp,
        usage=models.PowerUsage(value=usage_value),
        cost=models.PowerCost(value=cost_value),
        co2=models.CO2Emission(value=co2_value),
    )
    
    result = power_data.to_dict()
    
    # Check structure
    assert "period" in result
    assert "timestamp" in result
    assert "usage" in result
    assert "cost" in result
    assert "co2" in result
    
    # Check values
    assert result["period"] == period
    assert result["usage"] == usage_value
    assert result["cost"] == cost_value
    assert result["co2"] == co2_value


@given(
    period=period_strategy,
    usage_value=positive_floats,
    cost_value=positive_floats,
    co2_value=positive_floats,
)
def test_power_data_to_dict_timestamp_is_iso_format(
    period, usage_value, cost_value, co2_value
):
    """Property: PowerData.to_dict() timestamp is ISO format string."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    power_data = models.PowerData(
        period=period,
        timestamp=timestamp,
        usage=models.PowerUsage(value=usage_value),
        cost=models.PowerCost(value=cost_value),
        co2=models.CO2Emission(value=co2_value),
    )
    
    result = power_data.to_dict()
    
    # Timestamp should be ISO format string
    assert isinstance(result["timestamp"], str)
    # Should be parseable back to datetime
    parsed = datetime.fromisoformat(result["timestamp"])
    assert parsed == timestamp


# =============================================================================
# Exception Properties
# =============================================================================

@given(message=st.text(min_size=1, max_size=100))
def test_enecoq_error_message_preserved(message):
    """Property: EnecoQError preserves the message."""
    error = exceptions.EnecoQError(message)
    assert error.message == message
    assert message in str(error)


@given(
    message=st.text(min_size=1, max_size=100),
    code=st.text(min_size=1, max_size=20, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ_"),
)
def test_enecoq_error_with_code_format(message, code):
    """Property: EnecoQError with code formats correctly."""
    error = exceptions.EnecoQError(message, code)
    assert error.message == message
    assert error.error_code == code
    # String representation should include code in brackets
    assert "[%s]" % code in str(error)
    assert message in str(error)


@given(message=st.text(min_size=1, max_size=100))
def test_authentication_error_is_enecoq_error(message):
    """Property: AuthenticationError is subclass of EnecoQError."""
    error = exceptions.AuthenticationError(message)
    assert isinstance(error, exceptions.EnecoQError)
    assert isinstance(error, Exception)


@given(message=st.text(min_size=1, max_size=100))
def test_fetch_error_is_enecoq_error(message):
    """Property: FetchError is subclass of EnecoQError."""
    error = exceptions.FetchError(message)
    assert isinstance(error, exceptions.EnecoQError)
    assert isinstance(error, Exception)


@given(message=st.text(min_size=1, max_size=100))
def test_export_error_is_enecoq_error(message):
    """Property: ExportError is subclass of EnecoQError."""
    error = exceptions.ExportError(message)
    assert isinstance(error, exceptions.EnecoQError)
    assert isinstance(error, Exception)


# =============================================================================
# JSON Serialization Properties
# =============================================================================

@given(
    period=period_strategy,
    usage_value=positive_floats,
    cost_value=positive_floats,
    co2_value=positive_floats,
)
def test_power_data_json_serializable(period, usage_value, cost_value, co2_value):
    """Property: PowerData.to_dict() result is JSON serializable."""
    import json
    
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    power_data = models.PowerData(
        period=period,
        timestamp=timestamp,
        usage=models.PowerUsage(value=usage_value),
        cost=models.PowerCost(value=cost_value),
        co2=models.CO2Emission(value=co2_value),
    )
    
    result = power_data.to_dict()
    
    # Should not raise exception
    json_str = json.dumps(result)
    assert json_str is not None
    
    # Should be deserializable
    loaded = json.loads(json_str)
    assert loaded["period"] == period
    assert loaded["usage"] == usage_value
    assert loaded["cost"] == cost_value
    assert loaded["co2"] == co2_value


if __name__ == "__main__":
    print("Running property-based tests...\n")
    
    # Run all tests
    test_power_usage_value_preserved()
    print("✓ test_power_usage_value_preserved passed")
    
    test_power_usage_to_dict_returns_value()
    print("✓ test_power_usage_to_dict_returns_value passed")
    
    test_power_usage_custom_unit_preserved()
    print("✓ test_power_usage_custom_unit_preserved passed")
    
    test_power_cost_value_preserved()
    print("✓ test_power_cost_value_preserved passed")
    
    test_power_cost_to_dict_returns_value()
    print("✓ test_power_cost_to_dict_returns_value passed")
    
    test_power_cost_custom_unit_preserved()
    print("✓ test_power_cost_custom_unit_preserved passed")
    
    test_co2_emission_value_preserved()
    print("✓ test_co2_emission_value_preserved passed")
    
    test_co2_emission_to_dict_returns_value()
    print("✓ test_co2_emission_to_dict_returns_value passed")
    
    test_power_data_preserves_all_values()
    print("✓ test_power_data_preserves_all_values passed")
    
    test_power_data_to_dict_structure()
    print("✓ test_power_data_to_dict_structure passed")
    
    test_power_data_to_dict_timestamp_is_iso_format()
    print("✓ test_power_data_to_dict_timestamp_is_iso_format passed")
    
    test_enecoq_error_message_preserved()
    print("✓ test_enecoq_error_message_preserved passed")
    
    test_enecoq_error_with_code_format()
    print("✓ test_enecoq_error_with_code_format passed")
    
    test_authentication_error_is_enecoq_error()
    print("✓ test_authentication_error_is_enecoq_error passed")
    
    test_fetch_error_is_enecoq_error()
    print("✓ test_fetch_error_is_enecoq_error passed")
    
    test_export_error_is_enecoq_error()
    print("✓ test_export_error_is_enecoq_error passed")
    
    test_power_data_json_serializable()
    print("✓ test_power_data_json_serializable passed")
    
    print("\n✓ All property-based tests passed!")
