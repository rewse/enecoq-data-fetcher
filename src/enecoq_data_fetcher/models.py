"""Data models for power data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class PowerUsage:
    """Power usage data in kWh."""

    value: float
    unit: str = "kWh"

    def to_dict(self) -> float:
        """Convert to numeric value for JSON serialization.

        Returns:
            Numeric value without unit for JSON output.
        """
        return self.value


@dataclass
class PowerCost:
    """Power cost data in JPY."""

    value: float
    unit: str = "円"

    def to_dict(self) -> float:
        """Convert to numeric value for JSON serialization.

        Returns:
            Numeric value without unit for JSON output.
        """
        return self.value


@dataclass
class CO2Emission:
    """CO2 emission data in kg."""

    value: float
    unit: str = "kg"

    def to_dict(self) -> float:
        """Convert to numeric value for JSON serialization.

        Returns:
            Numeric value without unit for JSON output.
        """
        return self.value


@dataclass
class PowerData:
    """Complete power data.

    Attributes:
        period: Data period ("today" or "month").
        timestamp: Data acquisition timestamp.
        usage: Power usage data.
        cost: Power cost data.
        co2: CO2 emission data.
    """

    period: str
    timestamp: datetime
    usage: PowerUsage
    cost: PowerCost
    co2: CO2Emission

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with numeric values without units.
        """
        return {
            "period": self.period,
            "timestamp": self.timestamp.isoformat(),
            "usage": self.usage.to_dict(),
            "cost": self.cost.to_dict(),
            "co2": self.co2.to_dict(),
        }
