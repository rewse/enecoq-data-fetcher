"""Data exporter for power data."""

import json
import sys
from pathlib import Path
from typing import Optional

from enecoq_data_fetcher import exceptions
from enecoq_data_fetcher import logger
from enecoq_data_fetcher import models


class DataExporter:
    """Exporter for power data.

    Handles exporting power data to various formats including JSON and console.
    """

    def __init__(self):
        """Initialize exporter."""
        self._log = logger.get_logger()

    def export_json(
        self,
        data: models.PowerData,
        output_path: Optional[str] = None,
    ) -> str:
        """Export data as JSON.

        Args:
            data: PowerData object to export.
            output_path: Optional file path to save JSON. If None, returns JSON
                string without saving to file.

        Returns:
            JSON string representation of the data.

        Raises:
            ExportError: If file writing fails.
        """
        try:
            self._log.debug("Converting data to dictionary")
            # Convert data to dictionary with acquisition timestamp metadata
            data_dict = data.to_dict()

            # Format JSON with proper indentation
            self._log.debug("Serializing data to JSON")
            json_str = json.dumps(
                data_dict,
                ensure_ascii=False,
                indent=2,
            )

            # Write to file if path is provided
            if output_path:
                self._log.info("Writing JSON to file: %s", output_path)
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(json_str, encoding="utf-8")
                self._log.debug("JSON successfully written to: %s", output_path)
            else:
                self._log.debug("Outputting JSON to stdout")
                print(json_str)

            return json_str

        except (OSError, IOError) as e:
            self._log.error("Failed to export JSON: %s", e, exc_info=True)
            raise exceptions.ExportError(
                "Failed to export JSON: %s" % e
            ) from e
        except (TypeError, ValueError) as e:
            self._log.error("Failed to serialize data to JSON: %s", e, exc_info=True)
            raise exceptions.ExportError(
                "Failed to serialize data to JSON: %s" % e
            ) from e

    def export_console(self, data: models.PowerData) -> None:
        """Display data in console.

        Args:
            data: PowerData object to display.
        """
        self._log.info("Exporting data to console")
        
        # Print header
        print("=" * 30)
        print("enecoQ Data")
        print("=" * 30)
        print()

        # Print period and acquisition timestamp
        print("Period: %s" % data.period)
        print("Timestamp: %s" % data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        print()

        # Print power usage
        print("Power Usage: %s %s" % (data.usage.value, data.usage.unit))

        # Print power cost
        print("Power Cost: %s %s" % (data.cost.value, data.cost.unit))

        # Print CO2 emission
        print("CO2 Emission: %s %s" % (data.co2.value, data.co2.unit))

        print()
        print("=" * 30)

        # Flush output to ensure immediate display
        sys.stdout.flush()
        
        self._log.debug("Console export completed")
