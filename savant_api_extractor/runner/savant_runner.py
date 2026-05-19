"""Runner for orchestrating the Savant API extraction process."""

from __future__ import annotations

import logging
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd
from pandas.core.frame import DataFrame
from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


@contextmanager
def _route_stdout_log_handlers_through_live() -> Iterator[None]:
    """Repoint every stdout-bound logging.StreamHandler at the current
    ``sys.stdout`` for the duration of the context.

    ``rich.live.Live`` redirects ``sys.stdout`` while active so log lines
    written through it interleave cleanly above the live region. But any
    existing ``logging.StreamHandler(sys.stdout)`` cached the *original*
    stdout at construction time, so its writes bypass the redirect and
    tear the progress bars. Swapping their stream to the now-redirected
    ``sys.stdout`` makes log output flow through rich without tearing.
    """
    restorations: list[tuple[logging.StreamHandler, object]] = []
    seen: set[int] = set()
    logger_names = ["root", *logging.Logger.manager.loggerDict.keys()]
    for name in logger_names:
        lg = logging.getLogger(None if name == "root" else name)
        for h in lg.handlers:
            if (
                isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
                and id(h) not in seen
            ):
                seen.add(id(h))
                restorations.append((h, h.stream))
                h.setStream(sys.stdout)
    try:
        yield
    finally:
        for handler, original in restorations:
            handler.setStream(original)

from savant_api_extractor.controller.savant_controller import (
    OPP_HAND_SPLITS,
    SavantController,
)
from savant_api_extractor.handlers.leaderboard_handler import LeaderboardHandler
from savant_api_extractor.handlers.rolling_handler import RollingHandler
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
            include_leaderboards: Whether to pull the ETL-tier leaderboards and
                the rolling-windows leaderboard alongside the statcast_search
                splits. Defaults to True. Set False to run a splits-only
                extraction (useful for iterating on splits behavior).
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
        self.rolling_handler: RollingHandler = RollingHandler()
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

        Every HTTP fetch a run makes — the statcast_search handedness splits,
        the ETL-tier leaderboard pulls, and the state-inlined rolling-windows
        leaderboard — is dispatched through a single thread pool so they
        interleave instead of running as sequential phases. The pool is
        capped at `FETCH_MAX_WORKERS` to stay polite to Savant.

        Returns:
            Dictionary of DataFrames keyed by "batters"/"pitchers" (the
            statcast_search splits), by `config.name` (the leaderboards), and
            "rolling" (the rolling-windows leaderboard).
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

                # The rolling-windows leaderboard is state-inlined SSR, not a
                # CSV endpoint — its own handler, but it joins the same pool
                # and the same name-keyed result routing (-> savant_rolling_*).
                rolling_fut = ex.submit(self.rolling_handler.extract)
                lb_futures[rolling_fut] = "rolling"

            all_futures = [*split_futures, *lb_futures]
            fetch_start = time.perf_counter()

            # Two separate Progress instances grouped in a Live render so the
            # per-group bars (Splits / Leaderboards) stay above the overall
            # total bar regardless of which future finishes first.
            # A single Console is shared so the bars and any log lines emitted
            # during the fetch render through the same Live region without
            # tearing.
            console = Console()
            progress_columns = (
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
            )
            group_progress = Progress(
                *progress_columns, console=console, transient=False
            )
            overall_progress = Progress(
                *progress_columns, console=console, transient=False
            )

            with Live(
                Group(group_progress, overall_progress),
                console=console,
                refresh_per_second=10,
                redirect_stdout=True,
                redirect_stderr=True,
            ), _route_stdout_log_handlers_through_live():
                splits_task = group_progress.add_task(
                    "Splits", total=len(split_futures)
                )
                lb_task = (
                    group_progress.add_task(
                        "Leaderboards", total=len(lb_futures)
                    )
                    if lb_futures
                    else None
                )
                overall_task = overall_progress.add_task(
                    "Total progress", total=len(all_futures)
                )

                for fut in as_completed(all_futures):
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
                        group_progress.advance(splits_task)
                    else:
                        # Reaching this branch implies lb_futures is
                        # non-empty (the future came out of it), so lb_task
                        # was created above.
                        assert lb_task is not None
                        results[lb_futures[fut]] = frame
                        group_progress.advance(lb_task)
                    overall_progress.advance(overall_task)

            fetch_elapsed = time.perf_counter() - fetch_start
            self.logger.info(
                f"Fetched {len(all_futures)} Savant payloads in {fetch_elapsed:.1f}s"
            )

        # Concatenate each role's three splits in canonical all->R->L order.
        for role, by_hand in split_frames.items():
            results[role] = pd.concat(
                [by_hand[h] for h in OPP_HAND_SPLITS], ignore_index=True
            )

        self._export_to_json(results)
        return results
