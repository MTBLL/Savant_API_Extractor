"""Integration test for the MLB StatsAPI probable-pitchers fetch.

Hits the **live** StatsAPI schedule endpoint and asserts the per-game dict
shape `_game_to_row` projects is unchanged. Uses a fixed historical in-season
date — past dates always return a full slate, so the test is stable
year-round; it validates the response *shape*, which is date-independent.

Marked `integration` — excluded from the default `pytest tests/` run. Run
with `pytest -m integration`.
"""

from __future__ import annotations

import pytest

from savant_api_extractor.mlb_statsapi.probable_pitchers import (
    fetch_probable_pitchers,
)

pytestmark = pytest.mark.integration

# A fixed in-season date with a full MLB slate. Past dates always return
# data, so this test does not depend on when it runs.
_KNOWN_SLATE_DATE = "2024-08-15"

# The key set `_game_to_row` projects each StatsAPI game into.
_EXPECTED_KEYS = {
    "gamePk",
    "gameDate",
    "gameState",
    "away_team_code",
    "away_team_name",
    "away_probable_id",
    "away_probable_name",
    "home_team_code",
    "home_team_name",
    "home_probable_id",
    "home_probable_name",
}


def test_probable_pitchers_live_shape() -> None:
    """The live StatsAPI schedule response still yields per-game dicts with
    the documented key set. A schedule-payload shape change (renamed nesting,
    moved fields) surfaces here — `_game_to_row` would `KeyError`, or a key
    would go missing."""
    games = fetch_probable_pitchers(_KNOWN_SLATE_DATE)

    assert isinstance(games, list)
    assert len(games) > 0, f"no games returned for {_KNOWN_SLATE_DATE}"

    for game in games:
        assert set(game.keys()) == _EXPECTED_KEYS, (
            f"game {game.get('gamePk')}: key set {set(game.keys())} != "
            f"expected {_EXPECTED_KEYS} — StatsAPI response shape may have "
            f"changed"
        )
