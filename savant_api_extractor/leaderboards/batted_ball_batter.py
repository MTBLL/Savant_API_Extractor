"""Config for `/leaderboard/batted-ball?type=batter` — batted-ball profile per batter.

One row per batter with batted-ball-type rates (gb/air/fb/ld/pu), pull direction
rates (pull/straight/oppo), and the 6 combos (pull_gb_rate, pull_air_rate, etc.).

RT-tier — `pull_air_rate` is a well-known HR predictor (you need to pull AND
elevate to homer). Used as an HR drill-down when projecting a specific batter.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "id": "player_id",
    "name": "name",
    "bbe": "bbe",
    "gb_rate": "gb_rate",
    "air_rate": "air_rate",
    "fb_rate": "fb_rate",
    "ld_rate": "ld_rate",
    "pu_rate": "pu_rate",
    "pull_rate": "pull_rate",
    "straight_rate": "straight_rate",
    "oppo_rate": "oppo_rate",
    "pull_gb_rate": "pull_gb_rate",
    "straight_gb_rate": "straight_gb_rate",
    "oppo_gb_rate": "oppo_gb_rate",
    "pull_air_rate": "pull_air_rate",
    "straight_air_rate": "straight_air_rate",
    "oppo_air_rate": "oppo_air_rate",
}


CONFIG = LeaderboardConfig(
    name="batted_ball_batter",
    url_path="batted-ball",
    default_params={"type": "batter"},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id",),
)
