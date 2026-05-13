"""Config for `/leaderboard/pitcher-arm-angles` — release point / arm slot.

One row per pitcher with their average ball-release angle, release x/z
coordinates, and shoulder coordinates. Used for release-archetype classification
(over-the-top vs. three-quarters vs. sidearm vs. submarine).

RT-tier — pitcher-level metadata that rarely changes within a season, so it's
suitable for on-demand fetch when a matchup needs it.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "pitcher": "player_id",
    "pitcher_name": "name",
    "pitch_hand": "pitch_hand",
    "n_pitches": "n_pitches",
    "team_id": "team_id",
    "ball_angle": "ball_angle",
    "relative_release_ball_x": "release_ball_x_rel",
    "release_ball_z": "release_ball_z",
    "relative_shoulder_x": "shoulder_x_rel",
    "shoulder_z": "shoulder_z",
}


CONFIG = LeaderboardConfig(
    name="pitcher_arm_angles",
    url_path="pitcher-arm-angles",
    default_params={},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id",),
)
