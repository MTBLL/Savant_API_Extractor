"""Integration tests for the RT-tier leaderboard configs.

These hit the **live** Savant `/leaderboard/{slug}?csv=true` endpoints and
assert the response still carries every column each config's
`header_mappings` expects. The fixture unit tests
(`tests/handlers/test_leaderboard_handler.py`) prove the parse logic against
a frozen capture; these catch Savant *renaming or removing* a raw column —
which `LeaderboardHandler` would otherwise drop silently, leaving downstream
tables quietly missing data.

Marked `integration` — excluded from the default `pytest tests/` run (and
the pre-push coverage gate). Run with `pytest -m integration`.
"""

from __future__ import annotations

import pandas as pd
import pytest

from savant_api_extractor.handlers import LeaderboardHandler
from savant_api_extractor.leaderboards import RT_TIER_CONFIGS
from savant_api_extractor.leaderboards._config import LeaderboardConfig

pytestmark = pytest.mark.integration

# A completed season — full, stable data for every leaderboard.
_SEASON = "2025"
_NAME_PARSER_COLS = {"first_name", "last_name", "name_ascii", "slug"}


def _idfn(cfg: LeaderboardConfig) -> str:
    return cfg.name


@pytest.mark.parametrize("config", RT_TIER_CONFIGS, ids=_idfn)
def test_rt_leaderboard_live_shape(config: LeaderboardConfig) -> None:
    """The live endpoint still returns every column the config maps.

    The drift this catches: Savant renames a raw column, `LeaderboardHandler`
    drops it (unmapped, silent), and the output is quietly missing data with
    no error. Asserting the mapped column set is COMPLETE surfaces that.
    """
    df = LeaderboardHandler().extract(config, year=_SEASON)

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0, f"{config.name}: live endpoint returned no rows"

    expected = set(config.header_mappings.values())
    if "name" in expected:
        expected |= _NAME_PARSER_COLS

    missing = expected - set(df.columns)
    assert not missing, (
        f"{config.name}: live response is missing mapped columns {missing} "
        f"— Savant likely renamed/removed a raw column (the handler drops "
        f"unmapped columns silently)"
    )

    for col in config.identity_columns:
        assert col in df.columns, f"{config.name}: missing identity {col!r}"
        assert df[col].notna().all(), f"{config.name}: null values in {col!r}"
