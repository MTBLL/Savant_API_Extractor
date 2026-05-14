"""Runner for orchestrating the Savant API extraction process."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from pandas.core.frame import DataFrame

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

# One flat thread pool covers every HTTP fetch a run makes — the
# statcast_search handedness splits and the ETL-tier leaderboard pulls,
# interleaved rather than run as two sequential phases. Capped modest to
# stay polite to Savant; more concurrency risks rate-limiting, a worse
# outcome than a slightly slower run.
FETCH_MAX_WORKERS: int = 4


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

    def run(self) -> dict[str, DataFrame]:
        """
        Extract and export player statistics.

        Every HTTP fetch a run makes — the statcast_search handedness splits
        and the ETL-tier leaderboard pulls — is dispatched through a single
        thread pool so they interleave instead of running as two sequential
        phases. The pool is capped at `FETCH_MAX_WORKERS` to stay polite to
        Savant.

        Returns:
            Dictionary of DataFrames keyed by "batters"/"pitchers" (the
            statcast_search splits) and by `config.name` (the leaderboards).
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
        # statcast_search splits arrive per (role, opp_hand). Collect them
        # keyed by opp_hand so the per-role concat can run in a fixed
        # all->R->L order regardless of which future finishes first.
        split_frames: dict[str, dict[str, DataFrame]] = {
            extraction_map[et]: {} for et in extraction_types
        }

        self.logger.info(f"Dispatching fetches (max_workers={FETCH_MAX_WORKERS})")
        with ThreadPoolExecutor(max_workers=FETCH_MAX_WORKERS) as ex:
            split_futures: dict[Future[DataFrame], tuple[str, str]] = {}
            lb_futures: dict[Future[DataFrame], str] = {}

            # statcast_search handedness splits — 3 calls per role.
            for extraction_type in extraction_types:
                role = extraction_map[extraction_type]
                for opp_hand in OPP_HAND_SPLITS:
                    fut = ex.submit(
                        self.controller.extract,
                        extraction_type,
                        self.season,
                        opp_hand=opp_hand,
                    )
                    split_futures[fut] = (role, opp_hand)

            # ETL-tier leaderboards — one call per config, keyed by
            # `config.name` (which the JSONExporter turns into the output
            # filename `savant_{config.name}_{timestamp}.json`).
            if self.include_leaderboards:
                for cfg in ETL_TIER_CONFIGS:
                    fut = ex.submit(
                        self.leaderboard_handler.extract, cfg, year=self.season
                    )
                    lb_futures[fut] = cfg.name

            for fut in as_completed([*split_futures, *lb_futures]):
                try:
                    frame = fut.result()
                except Exception as e:
                    if fut in split_futures:
                        role, opp_hand = split_futures[fut]
                        label = f"split {role}/{opp_hand}"
                    else:
                        label = f"leaderboard {lb_futures[fut]}"
                    self.logger.error(f"Fetch failed [{label}]: {e}")
                    raise
                if fut in split_futures:
                    role, opp_hand = split_futures[fut]
                    split_frames[role][opp_hand] = frame
                else:
                    results[lb_futures[fut]] = frame

        # Concatenate each role's three splits in canonical all->R->L order.
        for role, by_hand in split_frames.items():
            results[role] = pd.concat(
                [by_hand[h] for h in OPP_HAND_SPLITS], ignore_index=True
            )

        self._export_to_json(results)
        return results
