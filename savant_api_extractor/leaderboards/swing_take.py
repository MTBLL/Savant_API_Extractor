"""Configs for `/leaderboard/swing-take` — Statcast Run Value Leaderboard.

Sums per-pitch run values across the season: positive = runs created
(batters) or runs prevented (pitchers). Wide-format — one row per player
with `runs_all` (season total) plus a zone decomposition (`runs_heart`,
`runs_shadow`, `runs_chase`, `runs_waste`).

Context-Neutral only (`leverage=Neutral`). The full canonical parameter
set is required: Savant's SSR template returns an empty dataset unless
`team`, `leverage`, `group`, `type`, `sub_type`, and `min` are all present
— a bare `?type=batter&csv=true` returns a header-only response. The
`group` parameter selects the role (`Batter` vs `Pitcher`) and is the only
param that differs between the two configs below.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig

# Both sides return identical columns; only the `group` param flips.
_HEADER_MAPPINGS = {
    "year": "year",
    "last_name, first_name": "name",
    "player_id": "player_id",
    "team_id": "team_id",
    "pa": "PA",
    "pitches": "pitches",
    "runs_all": "runs_all",
    "runs_heart": "runs_heart",
    "runs_shadow": "runs_shadow",
    "runs_chase": "runs_chase",
    "runs_waste": "runs_waste",
}

# Canonical param set required for a non-empty CSV response. `group` is
# filled in per-config; everything else is shared.
_BASE_PARAMS = {
    "team": "",
    "leverage": "Neutral",
    "type": "All",
    "sub_type": "null",
    "min": "q",
}


BATTER = LeaderboardConfig(
    name="swing_take_batter",
    url_path="swing-take",
    default_params={**_BASE_PARAMS, "group": "Batter"},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id", "year"),
)


PITCHER = LeaderboardConfig(
    name="swing_take_pitcher",
    url_path="swing-take",
    default_params={**_BASE_PARAMS, "group": "Pitcher"},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id", "year"),
)
