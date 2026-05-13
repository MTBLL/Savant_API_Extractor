"""Configs for `/leaderboard/expected_statistics` — Statcast x-stats.

Pitcher variant adds three ERA columns absent from the batter variant
(`era`, `xera`, `era_minus_xera_diff`); otherwise identical shape.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_BATTER_HEADER_MAPPINGS = {
    "last_name, first_name": "name",
    "player_id": "player_id",
    "year": "year",
    "pa": "PA",
    "bip": "BIP",
    "ba": "AVG",
    "est_ba": "xAVG",
    "est_ba_minus_ba_diff": "xAVGdiff",
    "slg": "SLG",
    "est_slg": "xSLG",
    "est_slg_minus_slg_diff": "xSLGdiff",
    "woba": "wOBA",
    "est_woba": "xwOBA",
    "est_woba_minus_woba_diff": "wOBAdiff",
}


_PITCHER_HEADER_MAPPINGS = {
    **_BATTER_HEADER_MAPPINGS,
    "era": "ERA",
    "xera": "xERA",
    "era_minus_xera_diff": "xERAdiff",
}


BATTER = LeaderboardConfig(
    name="expected_statistics_batter",
    url_path="expected_statistics",
    default_params={"type": "batter"},
    header_mappings=_BATTER_HEADER_MAPPINGS,
    identity_columns=("player_id", "year"),
)


PITCHER = LeaderboardConfig(
    name="expected_statistics_pitcher",
    url_path="expected_statistics",
    default_params={"type": "pitcher"},
    header_mappings=_PITCHER_HEADER_MAPPINGS,
    identity_columns=("player_id", "year"),
)
