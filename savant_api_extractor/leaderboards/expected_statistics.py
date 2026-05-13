"""Config for `/leaderboard/expected_statistics?type=pitcher` — pitcher x-stats.

The batter variant of this endpoint was dropped from ETL — every column it
provided is also returned by the `statcast_search` endpoint that feeds the
batter splits, so the leaderboard pull was redundant. The pitcher variant
is kept because it's the only source of `xERA` / `xERAdiff` in the entire
Savant catalog, which are the strongest single Statcast predictors of
fantasy ERA.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_PITCHER_HEADER_MAPPINGS = {
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
    "era": "ERA",
    "xera": "xERA",
    "era_minus_xera_diff": "xERAdiff",
}


PITCHER = LeaderboardConfig(
    name="expected_statistics_pitcher",
    url_path="expected_statistics",
    default_params={"type": "pitcher"},
    header_mappings=_PITCHER_HEADER_MAPPINGS,
    identity_columns=("player_id", "year"),
)
