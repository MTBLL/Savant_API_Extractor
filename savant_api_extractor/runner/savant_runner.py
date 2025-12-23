"""Runner for orchestrating the Savant API extraction process."""

import json
from pandas.core.frame import DataFrame
from pathlib import Path

import pandas as pd

from savant_api_extractor.controller.savant_controller import SavantController
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.logger import Logger
from savant_api_extractor.utils.thresholds import ThresholdType


class SavantRunner:
    """Runner that handles environment and orchestrates data extraction."""

    def __init__(
        self,
        season: str,
        extraction_type: str,
        threshold_type: ThresholdType = ThresholdType.DEFAULT,
        output_dir: Path | None = None,
        output_filename: str = "savant_data",
    ) -> None:
        """
        Initialize the runner.

        Args:
            output_dir: Directory to save output files (default: current directory)
        """
        self.logger: Logger = Logger(f"{__name__}.SavantRunner")
        self.extraction_method: ExtractionType = ExtractionType(extraction_type.lower())
        self.threshold_type: ThresholdType = threshold_type
        self.season: str = season

        self.controller: SavantController = SavantController(threshold_type)
        self.output_dir: Path = output_dir or Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filename: str = output_filename
        self.logger.info(f"Runner initialized with output directory: {self.output_dir}")

    def _export_to_json(
        self,
        data: pd.DataFrame | dict[str, pd.DataFrame],
    ) -> Path:
        """
        Export data to JSON file.

        Args:
            data: DataFrame or dictionary of DataFrames to export
            filename: Output filename (without extension)

        Returns:
            Path to the created JSON file
        """
        self.logger.info(f"Exporting data to JSON: {self.filename}")

        output_path = self.output_dir / f"{self.filename}.json"

        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to records format
            json_data = data.to_dict(orient="records")  # pyright: ignore[reportUnknownMemberType]
        else:
            # Convert dictionary of DataFrames to nested structure
            json_data = {
                key: df.to_dict(orient="records")  # pyright: ignore[reportUnknownMemberType]
                for key, df in data.items()
                }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, default=str)

        self.logger.info(f"Data exported to {output_path}")
        return output_path

    def run(
        self,
    ) -> dict[str, DataFrame]:
        """
        Extract and export player statistics.

        Args:
            threshold_type: Threshold type for minimum plate appearances
            season: Season year (e.g., "2025"). If None, uses current year logic.
            output_filename: Output filename (without extension)

        Returns:
            Dictionary of DataFrames keyed by "batters" and/or "pitchers"
        """
        self.logger.info("Running extraction")
        extraction_map = {
            ExtractionType.BATTER: "batters",
            ExtractionType.PITCHER: "pitchers",
        }

        if self.extraction_method == ExtractionType.ALL:
            extraction_types = list(extraction_map.keys())
        else:
            extraction_types = [self.extraction_method]

        results = {
            extraction_map[extraction_type]: self.controller.extract(
                extraction_type, self.season
            )
            for extraction_type in extraction_types
        }

        self._export_to_json(results)
        return results
