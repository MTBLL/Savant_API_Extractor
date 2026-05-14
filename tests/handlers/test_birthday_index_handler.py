"""Tests for the BirthdayIndexHandler.

The birthday-index page is state-inlined SSR — the dataset ships as a
`const birthdayData = [...];` assignment in the page HTML. These tests run
against a trimmed capture (`tests/fixtures/leaderboards/birthday_index.html`,
3 active + 2 inactive rows) so the extraction regex and the active-player
filter are both exercised against representative markup.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from savant_api_extractor.handlers.birthday_index_handler import (
    HEADER_MAPPINGS,
    IDENTITY_COLUMNS,
    BirthdayIndexHandler,
)


class TestBirthdayIndexHandler:
    def test_extract_parses_fixture(
        self, birthday_index_html_fixture: str
    ) -> None:
        """Handler parses the fixture into a DataFrame with the mapped columns."""
        handler = BirthdayIndexHandler()
        with patch.object(
            handler, "_fetch_html", return_value=birthday_index_html_fixture
        ):
            df = handler.extract()

        assert len(df) > 0
        for col in IDENTITY_COLUMNS:
            assert col in df.columns, f"missing identity column {col!r}"
        assert "birthday_index" in df.columns

    def test_extract_filters_to_active_players(
        self, birthday_index_html_fixture: str
    ) -> None:
        """The active-player filter is the headline requirement: the fixture
        has 3 active + 2 inactive rows; extract() must return only the 3
        active, and must not emit the `is_player_active` flag."""
        handler = BirthdayIndexHandler()
        with patch.object(
            handler, "_fetch_html", return_value=birthday_index_html_fixture
        ):
            df = handler.extract()

        # 3 active of the 5 fixture rows
        assert len(df) == 3
        # the filter inputs are not part of the output contract
        assert "is_player_active" not in df.columns
        assert "is_player_deceased" not in df.columns

    def test_header_mapping_drops_dupes_and_hidden(
        self, birthday_index_html_fixture: str
    ) -> None:
        """Redundant duplicates (`player_name`, `id`), `*_hidden` sort-helpers,
        and `dateString` are dropped; only HEADER_MAPPINGS targets plus the
        name-parser additions survive."""
        handler = BirthdayIndexHandler()
        with patch.object(
            handler, "_fetch_html", return_value=birthday_index_html_fixture
        ):
            df = handler.extract()

        for dropped in (
            "player_name",
            "id",
            "birth_day_noyear_sort_hidden",
            "curr_date_hidden",
            "dateString",
        ):
            assert dropped not in df.columns
        allowed = set(HEADER_MAPPINGS.values()) | {
            "first_name",
            "last_name",
            "name_ascii",
            "slug",
        }
        assert set(df.columns) <= allowed, (
            f"unexpected columns: {set(df.columns) - allowed}"
        )

    def test_name_parsing_applied(
        self, birthday_index_html_fixture: str
    ) -> None:
        """add_name_columns runs — the page's "First Last" name parses into
        first/last/ascii/slug."""
        handler = BirthdayIndexHandler()
        with patch.object(
            handler, "_fetch_html", return_value=birthday_index_html_fixture
        ):
            df = handler.extract()

        for col in ("first_name", "last_name", "name_ascii", "slug"):
            assert col in df.columns
        # Cole Young is the first active row in the captured fixture.
        row = df[df["name"] == "Cole Young"].iloc[0]
        assert row["first_name"] == "Cole"
        assert row["last_name"] == "Young"
        assert row["slug"] == "cole-young"

    def test_extract_rejects_invalid_player_type(self) -> None:
        """`player_type` must be 'batter' or 'pitcher' — anything else raises
        before any network call."""
        handler = BirthdayIndexHandler()
        with pytest.raises(ValueError, match="player_type must be one of"):
            handler.extract("infielder")

    def test_extract_passes_player_type_through(
        self, birthday_index_html_fixture: str
    ) -> None:
        """extract('pitcher') threads the type through to the fetch."""
        handler = BirthdayIndexHandler()
        with patch.object(
            handler, "_fetch_html", return_value=birthday_index_html_fixture
        ) as mock_fetch:
            handler.extract("pitcher")
        mock_fetch.assert_called_once_with("pitcher")

    def test_extract_handles_all_inactive_blob(self) -> None:
        """A blob with zero active players yields an empty DataFrame, not a
        crash — mirrors RollingHandler's empty-blob guard."""
        all_inactive = (
            "<script>const birthdayData = ["
            '{"is_player_active":0,"player_id":1,"name":"Retired Guy",'
            '"player_type":"Batter"}'
            "];const todayData = [];</script>"
        )
        handler = BirthdayIndexHandler()
        with patch.object(handler, "_fetch_html", return_value=all_inactive):
            df = handler.extract()
        assert df.empty

    def test_parse_blob_extracts_from_fixture(
        self, birthday_index_html_fixture: str
    ) -> None:
        """Regex-fragility guard (positive): the `const birthdayData = [...];`
        pattern matches the captured fixture — exercises the extraction regex
        against representative markup."""
        blob = BirthdayIndexHandler._parse_birthday_blob(
            birthday_index_html_fixture
        )
        # 3 active + 2 inactive in the fixture
        assert len(blob) == 5
        assert all("birthday_index" in row for row in blob)

    def test_parse_blob_raises_when_pattern_missing(self) -> None:
        """Regex-fragility guard (negative): the page uses `const` — if Savant
        switches to `var`/`let`, renames the variable, or moves to an XHR
        endpoint, the handler raises rather than silently returning empty."""
        # `var` instead of `const` — the regex no longer matches.
        broken_html = "<script>var birthdayData = [];</script>"
        with pytest.raises(ValueError, match="pattern not found"):
            BirthdayIndexHandler._parse_birthday_blob(broken_html)

    def test_fetch_html_returns_page_text(self) -> None:
        """_fetch_html GETs the birthday-index URL with the type param and
        returns the response text."""
        handler = BirthdayIndexHandler()
        with patch(
            "savant_api_extractor.handlers.birthday_index_handler.requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html>birthday page</html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            result = handler._fetch_html("pitcher")

        assert result == "<html>birthday page</html>"
        mock_get.assert_called_once_with(
            BirthdayIndexHandler.BIRTHDAY_INDEX_URL,
            params={"type": "pitcher"},
            timeout=30,
        )

    def test_fetch_html_raises_on_request_error(self) -> None:
        """Network errors from _fetch_html propagate as RequestException."""
        handler = BirthdayIndexHandler()
        with patch(
            "savant_api_extractor.handlers.birthday_index_handler.requests.get",
            side_effect=requests.exceptions.ConnectionError("boom"),
        ):
            with pytest.raises(requests.exceptions.ConnectionError):
                handler._fetch_html("batter")
