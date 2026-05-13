"""Runner for orchestrating the Savant API extraction process."""

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from pandas.core.frame import DataFrame
from pathlib import Path

from savant_api_extractor.controller.savant_controller import (
    OPP_HAND_SPLITS,
    SavantController,
)
from savant_api_extractor.handlers.leaderboard_handler import LeaderboardHandler
from savant_api_extractor.leaderboards import ETL_TIER_CONFIGS
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.json_exporter import JSONExporter
from savant_api_extractor.utils.logger import Logger
from savant_api_extractor.utils.thresholds import ThresholdType

# Parallelism for the leaderboard pulls — keep modest to stay polite to Savant.
LEADERBOARD_MAX_WORKERS: int = 4


class SavantRunner:
    """Runner that handles environment and orchestrates data extraction."""

    def __init__(
        self,
        season: str,
        extraction_type: str,
        threshold_type: ThresholdType = ThresholdType.DEFAULT,
        output_dir: Path | None = None,
        include_leaderboards: bool = True,
    ) -> None:
        """
        Initialize the runner.

        Args:
            season: Season year (e.g., "2025")
            extraction_type: Type of data to extract ("batters", "pitchers", "all")
            threshold_type: Threshold type for minimum plate appearances
            output_dir: Directory to save output files (default: current directory)
            include_leaderboards: Whether to pull ETL-tier leaderboards alongside
                the statcast_search splits. Defaults to True. Set False to run a
                splits-only extraction (useful for iterating on splits behavior).
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
        self.include_leaderboards: bool = include_leaderboards

        self.controller: SavantController = SavantController(threshold_type)
        self.leaderboard_handler: LeaderboardHandler = LeaderboardHandler()
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

        results: dict[str, DataFrame] = {}

        # statcast_search handedness splits (existing behavior — per-role,
        # 3 HTTP calls each, concatenated into one long-format DataFrame).
        for extraction_type in extraction_types:
            split_frames = [
                self.controller.extract(extraction_type, self.season, opp_hand=h)
                for h in OPP_HAND_SPLITS
            ]
            results[extraction_map[extraction_type]] = pd.concat(
                split_frames, ignore_index=True
            )

        # ETL-tier leaderboards (independent of extraction_method — these are
        # cross-cutting auxiliary tables, always pulled). Parallelized to keep
        # total wall time under 1 min.
        if self.include_leaderboards:
            results.update(self._extract_leaderboards())

        self._export_to_json(results)
        return results

    def _extract_leaderboards(self) -> dict[str, DataFrame]:
        """Pull all ETL-tier leaderboards in parallel.

        Each leaderboard becomes one entry in the returned dict, keyed by
        `config.name` (which the JSONExporter uses to construct the output
        filename — `savant_{config.name}_{timestamp}.json`).
        """
        self.logger.info(
            f"Pulling {len(ETL_TIER_CONFIGS)} ETL-tier leaderboards "
            f"(max_workers={LEADERBOARD_MAX_WORKERS})"
        )
        out: dict[str, DataFrame] = {}
        with ThreadPoolExecutor(max_workers=LEADERBOARD_MAX_WORKERS) as ex:
            future_to_config = {
                ex.submit(
                    self.leaderboard_handler.extract, cfg, year=self.season
                ): cfg
                for cfg in ETL_TIER_CONFIGS
            }
            for future in as_completed(future_to_config):
                cfg = future_to_config[future]
                try:
                    out[cfg.name] = future.result()
                except Exception as e:
                    self.logger.error(f"Leaderboard {cfg.name} failed: {e}")
                    raise
        return out
