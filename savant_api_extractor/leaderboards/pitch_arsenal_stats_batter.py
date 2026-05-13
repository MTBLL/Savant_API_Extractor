"""Config for `/leaderboard/pitch-arsenal-stats?type=batter` — per-pitch outcomes.

Returns one row per (player, pitch_type), giving batter outcome stats split
by what they faced. Keystone for matchup-projection lookups in the analytics
app: combine with a pitcher's per-pitch arsenal to project at-bat outcomes.

Pitcher variant lives in a separate config module (MTBL-161 / PR-C).
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "last_name, first_name": "name",
    "player_id": "player_id",
    "team_name_alt": "team",
    "pitch_type": "pitch_type",
    "pitch_name": "pitch_name",
    "run_value_per_100": "run_value_per_100",
    "run_value": "run_value",
    "pitches": "pitches",
    "pitch_usage": "pitch_usage_pct",
    "pa": "PA",
    "ba": "AVG",
    "slg": "SLG",
    "woba": "wOBA",
    "whiff_percent": "whiff_pct",
    "k_percent": "K%",
    "put_away": "put_away_pct",
    "est_ba": "xAVG",
    "est_slg": "xSLG",
    "est_woba": "xwOBA",
    "hard_hit_percent": "hardhit_pct",
}


BATTER = LeaderboardConfig(
    name="pitch_arsenal_stats_batter",
    url_path="pitch-arsenal-stats",
    default_params={"type": "batter"},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id", "pitch_type"),
)
