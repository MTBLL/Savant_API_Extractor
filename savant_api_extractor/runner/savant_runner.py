"""Runner for orchestrating the Savant API extraction process."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from savant_api_extractor.controller.savant_controller import SavantController
from savant_api_extractor.utils.logger import Logger


class SavantRunner:
    """Runner that handles environment and orchestrates data extraction."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """
        Initialize the runner.

        Args:
            output_dir: Directory to save output files (default: current directory)
        """
        self.logger = Logger(f"{__name__}.SavantRunner")
        self.controller = SavantController()
        self.output_dir = output_dir or Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Runner initialized with output directory: {self.output_dir}")

    def export_to_json(
        self,
        data: pd.DataFrame | dict[str, pd.DataFrame],
        filename: str,
    ) -> Path:
        """
        Export data to JSON file.

        Args:
            data: DataFrame or dictionary of DataFrames to export
            filename: Output filename (without extension)

        Returns:
            Path to the created JSON file
        """
        self.logger.info(f"Exporting data to JSON: {filename}")

        output_path = self.output_dir / f"{filename}.json"

        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to records format
            json_data: Any = data.to_dict(orient="records")
        else:
            # Convert dictionary of DataFrames to nested structure
            json_data = {
                key: df.to_dict(orient="records") for key, df in data.items()
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, default=str)

        self.logger.info(f"Data exported to {output_path}")
        return output_path

    def run_batters(
        self,
        query_params: dict[str, Any],
        output_filename: str = "batters",
    ) -> Path:
        """
        Extract and export batter statistics.

        Args:
            query_params: Query parameters for the API request
            output_filename: Output filename (without extension)

        Returns:
            Path to the created JSON file
        """
        self.logger.info("Running batter extraction")
        df = self.controller.extract_batters(query_params)
        return self.export_to_json(df, output_filename)

    def run_pitchers(
        self,
        query_params: dict[str, Any],
        output_filename: str = "pitchers",
    ) -> Path:
        """
        Extract and export pitcher statistics.

        Args:
            query_params: Query parameters for the API request
            output_filename: Output filename (without extension)

        Returns:
            Path to the created JSON file
        """
        self.logger.info("Running pitcher extraction")
        df = self.controller.extract_pitchers(query_params)
        return self.export_to_json(df, output_filename)

    def run_all(
        self,
        batter_params: dict[str, Any] | None = None,
        pitcher_params: dict[str, Any] | None = None,
        output_filename: str = "savant_data",
    ) -> Path:
        """
        Extract and export both batter and pitcher statistics.

        Args:
            batter_params: Query parameters for batters (optional)
            pitcher_params: Query parameters for pitchers (optional)
            output_filename: Output filename (without extension)

        Returns:
            Path to the created JSON file
        """
        self.logger.info("Running full extraction")
        results = self.controller.extract_all(batter_params, pitcher_params)
        return self.export_to_json(results, output_filename)
