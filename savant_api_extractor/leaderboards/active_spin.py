"""Config for `/leaderboard/active-spin` — active-spin % per pitch type per pitcher.

**Wide-format on pitch type**: one row per pitcher, with a column per pitch
type containing the percentage of the pitch's total spin that contributes to
movement (vs. gyroscopic spin that doesn't). NaN for pitch types not thrown.

RT-tier — paired with `pitch_arsenals` (velocity) and `pitch_movement` (break)
to fully describe a pitcher's per-pitch profile. Raw column names use full
pitch-type words (`active_spin_fourseam`, `active_spin_curve`); normalized
to pitch-type codes (`ff`, `cu`) for join consistency with the other two.
"""

from __future__ import annotations

from savant_api_extractor.leaderboards._config import LeaderboardConfig


_HEADER_MAPPINGS = {
    "entity_name": "name",
    "entity_id": "player_id",
    "pitch_hand": "pitch_hand",
    "active_spin_fourseam": "active_spin_ff",
    "active_spin_sinker": "active_spin_si",
    "active_spin_cutter": "active_spin_fc",
    "active_spin_changeup": "active_spin_ch",
    "active_spin_splitter": "active_spin_fs",
    "active_spin_curve": "active_spin_cu",
    "active_spin_slider": "active_spin_sl",
    "active_spin_sweeper": "active_spin_st",
    "active_spin_slurve": "active_spin_sv",
}


CONFIG = LeaderboardConfig(
    name="active_spin",
    url_path="active-spin",
    default_params={},
    header_mappings=_HEADER_MAPPINGS,
    identity_columns=("player_id",),
)
