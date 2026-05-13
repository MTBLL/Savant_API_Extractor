"""LeaderboardConfig dataclass — one instance per Savant CSV leaderboard endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class LeaderboardConfig:
    """Declarative description of a single Savant leaderboard endpoint.

    Each `leaderboards/{slug}.py` config module instantiates one or more of
    these (e.g., BATTER + PITCHER variants of the same `url_path`). The
    generic `LeaderboardHandler` consumes a config to build the request URL,
    parse the CSV, and normalize the column names.
    """

    name: str
    """Short slug used for logging and as the output JSON filename stem,
    e.g. `statcast_batter` → `savant_statcast_batter_YYYY_MM_DD_HHMM.json`."""

    url_path: str
    """The leaderboard slug appended to the Savant leaderboard base URL,
    e.g. `statcast`, `expected_statistics`, `pitch-arsenal-stats`."""

    default_params: Mapping[str, str]
    """Static query parameters baked into this config (excluding `csv=true`
    which the handler always adds). Type variants (batter vs pitcher) and
    other endpoint-specific knobs live here. Per-call overrides like `year`
    are passed as kwargs to `LeaderboardHandler.extract`."""

    header_mappings: Mapping[str, str]
    """Raw-CSV column name → normalized name. Columns absent from this
    mapping are dropped from the output DataFrame, mirroring the existing
    batter/pitcher handler convention."""

    identity_columns: tuple[str, ...]
    """The natural-key columns of this leaderboard's output rows. Used
    downstream to define DuckDB primary keys and join conditions. E.g.,
    `statcast` is one row per player (`("player_id",)`); `pitch-arsenal-stats`
    is long on pitch type (`("player_id", "pitch_type")`)."""
