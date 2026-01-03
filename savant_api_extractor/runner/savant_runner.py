"""Runner for orchestrating the Savant API extraction process."""

from pandas.core.frame import DataFrame
from pathlib import Path

from savant_api_extractor.controller.savant_controller import SavantController
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.json_exporter import JSONExporter
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
    ) -> None:
        """
        Initialize the runner.

        Args:
            season: Season year (e.g., "2025")
            extraction_type: Type of data to extract ("batters", "pitchers", "all")
            threshold_type: Threshold type for minimum plate appearances
            output_dir: Directory to save output files (default: current directory)
        """
        self.logger: Logger = Logger(f"{__name__}.SavantRunner")
        normalized_type = extraction_type.lower()
        normalized_type = {
            "batter": "batters",
            "pitcher": "pitchers",
        }.get(normalized_type, normalized_type)
        self.extraction_method: ExtractionType = ExtractionType(normalized_type)
        self.threshold_type: ThresholdType = threshold_type
        self.season: str = season

        self.controller: SavantController = SavantController(threshold_type)
        self.output_dir: Path = output_dir or Path.cwd()
        self.exporter: JSONExporter = JSONExporter(self.output_dir)
        self.logger.info(f"Runner initialized with output directory: {self.output_dir}")

    def _export_to_json(
        self,
        data: DataFrame | dict[str, DataFrame],
    ) -> list[Path]:
        """
        Export data to JSON file(s) using the JSONExporter utility.

        Args:
            data: DataFrame or dictionary of DataFrames to export

        Returns:
            List of paths to the created JSON file(s)
        """
        return self.exporter.export(data)

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
