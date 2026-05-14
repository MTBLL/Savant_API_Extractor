"""Tests for the RollingHandler.

The rolling-windows leaderboard is state-inlined SSR — the dataset ships as
a `var rolling = {...};` assignment inside the page HTML. These tests run
against a trimmed capture of that HTML (`tests/fixtures/leaderboards/
rolling.html`) so the extraction regex is exercised against representative
markup, and a guard test fails loudly if Savant changes the template.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from savant_api_extractor.handlers.rolling_handler import (
    HEADER_MAPPINGS,
    IDENTITY_COLUMNS,
    RollingHandler,
)

_EXPECTED_CATEGORIES = {
    "Batter50",
    "Batter100",
    "Batter250",
    "Pitcher50",
    "Pitcher100",
    "Pitcher250",
}


class TestRollingHandler:
    def test_extract_parses_fixture_to_long_format(
        self, rolling_html_fixture: str
    ) -> None:
        """Handler returns ONE long-format DataFrame (not 6 frames) with all
        6 (role x window) categories present."""
        handler = RollingHandler()
        with patch.object(
            handler, "_fetch_html", return_value=rolling_html_fixture
        ):
            df = handler.extract()

        assert set(df["cat"].unique()) == {"Batter", "Pitcher"}
        assert set(df["cat_bin"].unique()) == {"50", "100", "250"}
        # 6 categories x 3 rows each in the trimmed fixture
        assert len(df) == 18

        for col in IDENTITY_COLUMNS:
            assert col in df.columns, f"missing identity column {col!r}"

    def test_header_mapping_applied(self, rolling_html_fixture: str) -> None:
        """Raw columns renamed per HEADER_MAPPINGS; unmapped columns dropped."""
        handler = RollingHandler()
        with patch.object(
            handler, "_fetch_html", return_value=rolling_html_fixture
        ):
            df = handler.extract()

        # Stat triples renamed to conventional casing.
        for renamed in ("last_xwOBA", "prev_xwOBA", "xwOBA_delta", "last_BA"):
            assert renamed in df.columns
        # Raw names gone.
        for raw in ("last_x_xwoba", "penultimate_x_xwoba", "xwoba_delta"):
            assert raw not in df.columns
        # player_name -> name.
        assert "name" in df.columns and "player_name" not in df.columns
        # Unmapped Savant columns dropped (type_cat_bin is redundant with
        # cat + cat_bin; Savant's own slug conflicts with our format).
        assert "type_cat_bin" not in df.columns
        # Every output column is a mapping target or a name-parser addition.
        allowed = set(HEADER_MAPPINGS.values()) | {
            "first_name",
            "last_name",
            "name_ascii",
            "slug",
        }
        assert set(df.columns) <= allowed, (
            f"unexpected columns: {set(df.columns) - allowed}"
        )

    def test_name_parsing_applied(self, rolling_html_fixture: str) -> None:
        """add_name_columns runs — first/last/ascii/slug derived from `name`."""
        handler = RollingHandler()
        with patch.object(
            handler, "_fetch_html", return_value=rolling_html_fixture
        ):
            df = handler.extract()

        for col in ("first_name", "last_name", "name_ascii", "slug"):
            assert col in df.columns
        # Vientos, Mark is Batter50[0] in the captured fixture.
        row = df[df["name"] == "Vientos, Mark"].iloc[0]
        assert row["first_name"] == "Mark"
        assert row["last_name"] == "Vientos"
        assert row["name_ascii"] == "Mark Vientos"
        assert row["slug"] == "mark-vientos"

    def test_parse_blob_extracts_all_categories_from_fixture(
        self, rolling_html_fixture: str
    ) -> None:
        """Regex-fragility guard (positive): the `var rolling = {...};` pattern
        DOES match the captured fixture. Exercises the actual extraction regex
        against representative HTML — a future Savant template change that
        breaks the pattern is caught right here."""
        blob = RollingHandler._parse_rolling_blob(rolling_html_fixture)
        assert set(blob.keys()) == _EXPECTED_CATEGORIES
        assert all(len(rows) > 0 for rows in blob.values())

    def test_parse_blob_raises_loudly_when_pattern_missing(self) -> None:
        """Regex-fragility guard (negative): if Savant drops the `var rolling
        = {...};` shape (e.g. switches to `const`, renames, or moves to an XHR
        endpoint), the handler raises rather than silently returning empty."""
        # `const` instead of `var` — the regex no longer matches.
        broken_html = (
            "<script>const rolling = {\"Batter50\": []};</script>"
        )
        with pytest.raises(ValueError, match="pattern not found"):
            RollingHandler._parse_rolling_blob(broken_html)

    def test_extract_handles_all_empty_blob(self) -> None:
        """A valid blob whose 6 category lists are all empty yields an empty
        DataFrame, not a crash.

        Without the `if "name" in df.columns` guard, an all-empty blob makes
        `pd.DataFrame([])` column-less and `add_name_columns` asserts on the
        missing `name` column — aborting the whole run on an empty-result day.
        """
        empty_html = (
            "<script>var rolling = {"
            '"Batter50":[],"Pitcher50":[],"Batter100":[],'
            '"Pitcher100":[],"Batter250":[],"Pitcher250":[]'
            "};var query = {};</script>"
        )
        handler = RollingHandler()
        with patch.object(handler, "_fetch_html", return_value=empty_html):
            df = handler.extract()
        assert df.empty
        assert len(df) == 0

    def test_fetch_html_returns_page_text(self) -> None:
        """_fetch_html GETs the rolling URL and returns the response text."""
        handler = RollingHandler()
        with patch(
            "savant_api_extractor.handlers.rolling_handler.requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html>rolling page</html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            result = handler._fetch_html()

        assert result == "<html>rolling page</html>"
        mock_get.assert_called_once_with(
            RollingHandler.ROLLING_URL, timeout=30
        )

    def test_fetch_html_raises_on_request_error(self) -> None:
        """Network errors from _fetch_html propagate as RequestException."""
        handler = RollingHandler()
        with patch(
            "savant_api_extractor.handlers.rolling_handler.requests.get",
            side_effect=requests.exceptions.ConnectionError("boom"),
        ):
            with pytest.raises(requests.exceptions.ConnectionError):
                handler._fetch_html()
