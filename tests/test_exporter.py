"""Tests for exporter functionality."""

from datetime import datetime
from pathlib import Path

from enecoq_data_fetcher import exporter
from enecoq_data_fetcher import models


def test_export_json_string():
    """Test JSON export to string."""
    # Create test data
    test_data = models.PowerData(
        period="today",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )

    # Create exporter
    exp = exporter.DataExporter()

    # Test JSON string generation
    json_str = exp.export_json(test_data)
    print("JSON output:")
    print(json_str)
    print()

    # Verify JSON contains expected data
    assert "12.5" in json_str
    assert "350.0" in json_str
    assert "6.25" in json_str
    assert "2024-01-15T10:30:00" in json_str
    assert "today" in json_str
    print("✓ JSON string generation works")


def test_export_json_file():
    """Test JSON export to file."""
    # Create test data
    test_data = models.PowerData(
        period="today",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=12.5),
        cost=models.PowerCost(value=350.0),
        co2=models.CO2Emission(value=6.25),
    )

    # Create exporter
    exp = exporter.DataExporter()

    # Test JSON file export
    output_path = "test_output.json"
    json_str = exp.export_json(test_data, output_path)
    
    assert Path(output_path).exists()
    content = Path(output_path).read_text(encoding="utf-8")
    assert content == json_str
    print("✓ JSON file export works")

    # Cleanup
    Path(output_path).unlink()


def test_export_console():
    """Test console export functionality."""
    # Create test data
    test_data = models.PowerData(
        period="month",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        usage=models.PowerUsage(value=450.0),
        cost=models.PowerCost(value=12500.0),
        co2=models.CO2Emission(value=225.0),
    )

    # Create exporter
    exp = exporter.DataExporter()

    # Test console output
    print("Console output:")
    exp.export_console(test_data)
    print("✓ Console export works")


if __name__ == "__main__":
    test_export_json_string()
    test_export_json_file()
    test_export_console()
    print("\nAll tests passed!")
