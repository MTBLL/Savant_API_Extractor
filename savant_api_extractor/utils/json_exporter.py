"""JSON export utilities for Savant data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Hashable

import pandas as pd

from savant_api_extractor.utils.logger import Logger


class JSONExporter:
    """Handles exporting DataFrames to JSON files."""

    def __init__(self, output_dir: Path) -> None:
        """
        Initialize the JSON exporter.

        Args:
            output_dir: Directory to save output files
        """
        self.logger: Logger = Logger(f"{__name__}.JSONExporter")
        self.output_dir: Path = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        data: pd.DataFrame | dict[str, pd.DataFrame],
    ) -> list[Path]:
        """
        Export data to JSON file(s).

        Creates files with pattern: savant_<pos>_yyyy_mm_dd_hhmm.json
        where <pos> is 'batters' or 'pitchers'

        Args:
            data: DataFrame or dictionary of DataFrames to export

        Returns:
            List of paths to the created JSON file(s)
        """
        output_paths: list[Path] = []
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")

        for player_type, df in data.items():
            filename = f"savant_{player_type}_{timestamp}"
            assert isinstance(df, pd.DataFrame), f"Expected DataFrame, got {type(df)}"
            output_paths.append(self._export_single(df, filename))

        return output_paths

    def _export_single(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Export a single DataFrame to a JSON file.

        Args:
            df: DataFrame to export
            filename: Output filename (without extension)

        Returns:
            Path to the created JSON file
        """
        self.logger.info(f"Exporting data to JSON: {filename}")
        output_path = self.output_dir / f"{filename}.json"
        json_data: list[dict[Hashable, Any]] = df.to_dict(orient="records")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, default=str)

        self.logger.info(f"Data exported to {output_path}")
        return output_path
