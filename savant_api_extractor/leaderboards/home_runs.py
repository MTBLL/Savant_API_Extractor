"""Configs for `/leaderboard/home-runs` — HR / xHR / park-adjusted variants.

Same schema for batter and pitcher; default endpoint is batter-side
(HRs hit), `player_type=Pitcher` flips to HRs allowed. The `hr_type`
column distinguishes raw vs park-adjusted xHR row variants.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "player": "name",
    "player_id": "player_id",
    "team_abbrev": "team",
    "year": "year",
    "type": "hr_type",
    "avg_hr_trot": "avg_hr_trot",
    "doubters": "doubters",
    "mostly_gone": "mostly_gone",
    "no_doubters": "no_doubters",
    "no_doubter_per": "no_doubter_pct",
    "hr_total": "HR",
    "xhr": "xHR",
    "xhr_diff": "xHRdiff",
}


BATTER = LeaderboardConfig(
    name="home_runs_batter",
    url_path="home-runs",
    default_params={},  # endpoint defaults to batter side
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id", "year", "hr_type"),
)


PITCHER = LeaderboardConfig(
    name="home_runs_pitcher",
    url_path="home-runs",
    default_params={"player_type": "Pitcher"},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id", "year", "hr_type"),
)
