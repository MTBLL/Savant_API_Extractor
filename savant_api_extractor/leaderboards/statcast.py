"""Configs for `/leaderboard/statcast` — contact-quality leaderboard.

Same schema for batter and pitcher (it's the same endpoint with a `type`
filter); both produce one row per player with peak/avg exit velocity,
batted-ball distance, and barrel rates.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig

# Shared header mapping — batter and pitcher endpoint return identical columns
_HEADER_MAPPINGS = {
    "last_name, first_name": "name",
    "player_id": "player_id",
    "attempts": "bbe",  # batted ball events
    "avg_hit_angle": "avg_launch_angle",
    "anglesweetspotpercent": "sweetspot_pct",
    "max_hit_speed": "max_ev",
    "avg_hit_speed": "avg_ev",
    "ev50": "ev50",
    "fbld": "fbld_ev",  # avg ev on fly balls + line drives
    "gb": "gb_ev",  # avg ev on ground balls
    "max_distance": "max_distance",
    "avg_distance": "avg_distance",
    "avg_hr_distance": "avg_hr_distance",
    "ev95plus": "ev95_plus",
    "ev95percent": "ev95_pct",
    "barrels": "barrels",
    "brl_percent": "barrels_per_bbe_pct",
    "brl_pa": "barrels_per_pa_pct",
}


BATTER = LeaderboardConfig(
    name="statcast_batter",
    url_path="statcast",
    default_params={"type": "batter"},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id",),
)


PITCHER = LeaderboardConfig(
    name="statcast_pitcher",
    url_path="statcast",
    default_params={"type": "pitcher"},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id",),
)
