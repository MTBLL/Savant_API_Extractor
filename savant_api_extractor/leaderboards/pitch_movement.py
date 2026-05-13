"""Config for `/leaderboard/pitch-movement` — per-pitch movement vs league.

**Long-format on pitch type**: one row per (player_id, pitch_type, year) giving
the pitcher's actual break in inches plus the league-average break for that
pitch type, the diff, and percent-rank versions of both diffs.

RT-tier — strongest single proxy for "stuff" quality. Pairs with
`pitch_arsenals` (velocity) and `active_spin` (spin %) to fully describe a
pitcher's per-pitch profile for archetype matching.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "year": "year",
    "last_name, first_name": "name",
    "pitcher_id": "player_id",
    "team_name": "team_name",
    "team_name_abbrev": "team",
    "pitch_hand": "pitch_hand",
    "avg_speed": "avg_speed",
    "pitches_thrown": "pitches_thrown",
    "total_pitches": "total_pitches",
    "pitches_per_game": "pitches_per_game",
    "pitch_per": "pitch_per",
    "pitch_type": "pitch_type",
    "pitch_type_name": "pitch_name",
    "pitcher_break_z": "break_z",
    "league_break_z": "league_break_z",
    "diff_z": "diff_z",
    "rise": "rise",
    "pitcher_break_z_induced": "break_z_induced",
    "pitcher_break_x": "break_x",
    "league_break_x": "league_break_x",
    "diff_x": "diff_x",
    "tail": "tail",
    "percent_rank_diff_z": "pct_rank_diff_z",
    "percent_rank_diff_x": "pct_rank_diff_x",
}


CONFIG = LeaderboardConfig(
    name="pitch_movement",
    url_path="pitch-movement",
    default_params={},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id", "pitch_type", "year"),
)
