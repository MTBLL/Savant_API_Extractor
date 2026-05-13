"""Config for `/leaderboard/sprint_speed` — baserunning speed predictor for SB.

Returns sprint_speed (ft/sec, max-effort), bolts (count of 30+ ft/sec plays),
and home-to-first time. The single best Statcast predictor of SB volume in
fantasy projections.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "last_name, first_name": "name",
    "player_id": "player_id",
    "team_id": "team_id",
    "team": "team",
    "position": "position",
    "age": "age",
    "competitive_runs": "competitive_runs",
    "bolts": "bolts",
    "hp_to_1b": "hp_to_1b",
    "sprint_speed": "sprint_speed",
}


CONFIG = LeaderboardConfig(
    name="sprint_speed",
    url_path="sprint_speed",
    default_params={},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id",),
)
