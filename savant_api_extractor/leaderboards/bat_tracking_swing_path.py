"""Config for `/leaderboard/bat-tracking/swing-path-attack-angle` — batter swing diagnostics.

One row per (batter, batting side). Contains bat tracking metrics: average bat
speed, swing tilt, attack angle, attack direction, ideal-attack-angle rate,
plus intercept positioning (where the bat meets the ball relative to plate /
batter body).

RT-tier — drill-down for batter side. Used when analyzing a specific hitter's
swing profile in matchup context.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "id": "player_id",
    "name": "name",
    "side": "stands",
    "avg_bat_speed": "avg_bat_speed",
    "swing_tilt": "swing_tilt",
    "attack_angle": "attack_angle",
    "attack_direction": "attack_direction",
    "ideal_attack_angle_rate": "ideal_attack_angle_rate",
    "avg_intercept_y_vs_plate": "avg_intercept_y_vs_plate",
    "avg_intercept_y_vs_batter": "avg_intercept_y_vs_batter",
    "avg_batter_y_position": "avg_batter_y_position",
    "avg_batter_x_position": "avg_batter_x_position",
    "competitive_swings": "competitive_swings",
}


CONFIG = LeaderboardConfig(
    name="bat_tracking_swing_path",
    url_path="bat-tracking/swing-path-attack-angle",
    default_params={},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id", "stands"),
)
