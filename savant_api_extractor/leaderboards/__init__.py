"""Leaderboard endpoint configs.

Each `leaderboards/{slug}.py` module declares one or more `LeaderboardConfig`
instances. The generic `LeaderboardHandler` consumes a config to pull and
normalize that leaderboard's CSV.

Two tiers:

- `ETL_TIER_CONFIGS` is the curated list pulled on every scheduled extraction
  run by `SavantRunner`. These are the cross-cutting tables that every
  downstream consumer wants daily.
- `RT_TIER_CONFIGS` lives here for discoverability + parameterized tests but
  is **not invoked by the bulk runner**. The analytics app imports specific
  RT configs and calls `LeaderboardHandler.extract(config=...)` on demand
  when a matchup drill-down needs them. These should be cached client-side
  by the caller; this package is the network layer only.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards import (
    active_spin,
    bat_tracking_swing_path,
    batted_ball_batter,
    expected_statistics,
    home_runs,
    pitch_arsenal_stats,
    pitch_arsenals,
    pitch_movement,
    pitcher_arm_angles,
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

RT_TIER_CONFIGS: tuple[LeaderboardConfig, ...] = (
    pitch_arsenals.CONFIG,
    pitch_movement.CONFIG,
    active_spin.CONFIG,
    pitcher_arm_angles.CONFIG,
    bat_tracking_swing_path.CONFIG,
    batted_ball_batter.CONFIG,
)

__all__ = [
    "LeaderboardConfig",
    "ETL_TIER_CONFIGS",
    "RT_TIER_CONFIGS",
    # ETL config modules
    "statcast",
    "expected_statistics",
    "home_runs",
    "pitch_arsenal_stats",
    "sprint_speed",
    # RT config modules
    "pitch_arsenals",
    "pitch_movement",
    "active_spin",
    "pitcher_arm_angles",
    "bat_tracking_swing_path",
    "batted_ball_batter",
]
