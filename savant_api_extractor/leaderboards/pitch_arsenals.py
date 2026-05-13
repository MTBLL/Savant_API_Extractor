"""Config for `/leaderboard/pitch-arsenals` — per-pitch avg velocity per pitcher.

**Wide-format on pitch type**: one row per pitcher, with a separate column for
each pitch type's average release speed (ff/si/fc/sl/ch/cu/fs/kn/st/sv).
Cells are NaN for pitch types the pitcher doesn't throw.

RT-tier — the bulk runner doesn't pull this. Used by the analytics app for
pitcher-archetype lookups at matchup time. Pairs naturally with
`pitch_movement` and `active_spin` (same wide-on-pitch-type convention).
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "last_name, first_name": "name",
    "pitcher": "player_id",
    "ff_avg_speed": "ff_avg_speed",
    "si_avg_speed": "si_avg_speed",
    "fc_avg_speed": "fc_avg_speed",
    "sl_avg_speed": "sl_avg_speed",
    "ch_avg_speed": "ch_avg_speed",
    "cu_avg_speed": "cu_avg_speed",
    "fs_avg_speed": "fs_avg_speed",
    "kn_avg_speed": "kn_avg_speed",
    "st_avg_speed": "st_avg_speed",
    "sv_avg_speed": "sv_avg_speed",
}


CONFIG = LeaderboardConfig(
    name="pitch_arsenals",
    url_path="pitch-arsenals",
    default_params={},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id",),
)
