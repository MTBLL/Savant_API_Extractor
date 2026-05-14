"""Integration tests for the state-inlined SSR handlers.

These hit the **live** Savant pages and assert the inlined-JS extraction
still works and the parsed frame has the expected column shape. The headline
drift this catches: Savant changing a page template (`var rolling = {...}` /
`const birthdayData = [...]`) — which makes the handler's `_parse_*_blob`
raise `ValueError` loudly, exactly here, instead of in production.

Marked `integration` — excluded from the default `pytest tests/` run. Run
with `pytest -m integration`.
"""

from __future__ import annotations

import pytest

from savant_api_extractor.handlers import BirthdayIndexHandler, RollingHandler
from savant_api_extractor.handlers.birthday_index_handler import (
    HEADER_MAPPINGS as BIRTHDAY_HEADER_MAPPINGS,
)
from savant_api_extractor.handlers.rolling_handler import (
    HEADER_MAPPINGS as ROLLING_HEADER_MAPPINGS,
)

pytestmark = pytest.mark.integration

_NAME_PARSER_COLS = {"first_name", "last_name", "name_ascii", "slug"}


def test_rolling_live_shape() -> None:
    """RollingHandler still extracts `var rolling = {...}` from the live page,
    and the long-format frame carries every mapped column plus all 6
    (cat x cat_bin) categories. A template change makes `extract()` raise."""
    df = RollingHandler().extract()
    if df.empty:
        pytest.skip("rolling endpoint returned no rows (deep offseason?)")

    expected = set(ROLLING_HEADER_MAPPINGS.values()) | _NAME_PARSER_COLS
    missing = expected - set(df.columns)
    assert not missing, f"rolling: live response missing mapped columns {missing}"

    assert set(df["cat"].unique()) == {"Batter", "Pitcher"}
    assert set(df["cat_bin"].unique()) == {"50", "100", "250"}


@pytest.mark.parametrize("player_type", ["batter", "pitcher"])
def test_birthday_index_live_shape(player_type: str) -> None:
    """BirthdayIndexHandler still extracts `const birthdayData = [...]`, the
    active-player filter yields a non-empty frame, and every mapped column is
    present. A template change makes `extract()` raise."""
    df = BirthdayIndexHandler().extract(player_type)

    assert len(df) > 0, (
        f"birthday-index ({player_type}): no active players after the filter "
        f"— either an offseason lull or the active flag changed"
    )

    expected = set(BIRTHDAY_HEADER_MAPPINGS.values()) | _NAME_PARSER_COLS
    missing = expected - set(df.columns)
    assert not missing, (
        f"birthday-index ({player_type}): live response missing mapped "
        f"columns {missing}"
    )
