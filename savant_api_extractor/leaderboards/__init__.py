"""Leaderboard endpoint configs.

Each `leaderboards/{slug}.py` module declares one or more `LeaderboardConfig`
instances. The generic `LeaderboardHandler` consumes a config to pull and
normalize that leaderboard's CSV.

`ETL_TIER_CONFIGS` is the curated list pulled on every scheduled extraction
run. RT-tier configs (added in MTBL-161) will live alongside these but will
not be added to `ETL_TIER_CONFIGS` — they exist for the analytics app to
call on demand.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards import (
    expected_statistics,
    home_runs,
    pitch_arsenal_stats,
    sprint_speed,
    statcast,
)
from savant_api_extractor.leaderboards._config import LeaderboardConfig

ETL_TIER_CONFIGS: tuple[LeaderboardConfig, ...] = (
    statcast.BATTER,
    statcast.PITCHER,
    # expected_statistics.BATTER intentionally NOT pulled — every column it
    # provided is now in the batter splits export (`pa`/`ba` were added to
    # SHARED_HEADER_MAPPING; xAVG/xSLG/xwOBA/etc. were already there).
    expected_statistics.PITCHER,
    home_runs.BATTER,
    home_runs.PITCHER,
    pitch_arsenal_stats.BATTER,
    pitch_arsenal_stats.PITCHER,
    sprint_speed.CONFIG,
)

__all__ = [
    "LeaderboardConfig",
    "ETL_TIER_CONFIGS",
    "statcast",
    "expected_statistics",
    "home_runs",
    "pitch_arsenal_stats",
    "sprint_speed",
]
