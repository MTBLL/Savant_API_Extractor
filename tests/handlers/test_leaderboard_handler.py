"""Tests for the LeaderboardHandler.

One parameterized test exercises every ETL-tier config against its captured
fixture CSV — verifying that the handler renames columns per the config's
`header_mappings`, drops unmapped columns, and applies name-parsing when a
`name` column is present after renaming.

Ohtani is our cross-fixture anchor: he's present in all 8 ETL leaderboards
(he plays for LAD as both a batter and a pitcher in 2026), which makes him
the right identity column to assert on across the parameterized test.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from savant_api_extractor.handlers import LeaderboardHandler
from savant_api_extractor.leaderboards import ETL_TIER_CONFIGS
from savant_api_extractor.leaderboards._config import LeaderboardConfig


def _idfn(cfg: LeaderboardConfig) -> str:
    return cfg.name


class TestLeaderboardHandler:
    def test_initialization(self) -> None:
        handler = LeaderboardHandler()
        assert handler.name == "LeaderboardHandler"
        assert handler.logger is not None
        assert handler.LEADERBOARD_BASE.endswith("/leaderboard/")

    @pytest.mark.parametrize("config", ETL_TIER_CONFIGS, ids=_idfn)
    @patch("savant_api_extractor.handlers.base_handler.requests.get")
    def test_extract_parses_each_etl_fixture(
        self,
        mock_get: MagicMock,
        config: LeaderboardConfig,
        leaderboard_fixtures: dict[str, str],
    ) -> None:
        """Every ETL config produces a renamed DataFrame from its fixture."""
        mock_response = MagicMock()
        mock_response.text = leaderboard_fixtures[config.name]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = LeaderboardHandler()
        df = handler.extract(config, year="2026")

        # Non-empty frame
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        # Every column in the output should be a mapped target (or a name-
        # parser-added identity column when `name` is renamed in).
        mapped_targets = set(config.header_mappings.values())
        name_parser_cols = {"first_name", "last_name", "name_ascii", "slug"}
        allowed = mapped_targets | name_parser_cols
        assert set(df.columns) <= allowed, (
            f"Unexpected columns in {config.name}: "
            f"{set(df.columns) - allowed}"
        )

        # Identity columns from the config must all be present
        for identity_col in config.identity_columns:
            assert identity_col in df.columns, (
                f"Missing identity column {identity_col!r} in {config.name}"
            )

        # Percentile-rank columns are not emitted by leaderboard extracts
        assert not any(col.endswith("_pct_rnk") for col in df.columns)

        # When the config maps a name source column, name-parsing applies
        if "name" in mapped_targets:
            assert {"first_name", "last_name", "name_ascii", "slug"} <= set(
                df.columns
            )
            # Ohtani anchor: present in every ETL fixture (LAD two-way player)
            ohtani = df[df["name"] == "Ohtani, Shohei"]
            assert not ohtani.empty, f"Ohtani absent from {config.name}"
            row = ohtani.iloc[0]
            assert row["first_name"] == "Shohei"
            assert row["last_name"] == "Ohtani"
            assert row["name_ascii"] == "Shohei Ohtani"
            assert row["slug"] == "shohei-ohtani"

        # Confirm exactly one HTTP call per extract invocation
        mock_get.assert_called_once()
        # csv=true was injected into the params
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["csv"] == "true"
        # year override propagated through to the API call
        assert kwargs["params"]["year"] == "2026"

    @patch("savant_api_extractor.handlers.base_handler.requests.get")
    def test_extract_raises_on_request_error(
        self, mock_get: MagicMock, leaderboard_fixtures: dict[str, str]
    ) -> None:
        """Network errors propagate as RequestException."""
        mock_get.side_effect = requests.exceptions.ConnectionError("boom")
        handler = LeaderboardHandler()
        with pytest.raises(requests.exceptions.ConnectionError):
            handler.extract(ETL_TIER_CONFIGS[0])

    @patch("savant_api_extractor.handlers.base_handler.requests.get")
    def test_extract_skips_name_parsing_when_no_name_column(
        self, mock_get: MagicMock
    ) -> None:
        """If a config doesn't map any column to `name`, name-parser is skipped.

        Covers the False branch of the `if "name" in df.columns` conditional
        in LeaderboardHandler.extract. Every ETL-tier config maps either
        `last_name, first_name` or `player` to `name`, so this branch is
        never exercised by the parameterized test above. Future RT-tier
        configs that don't carry a name column (e.g., something keyed only
        on player_id + a discriminator) will travel this path.
        """
        minimal_config = LeaderboardConfig(
            name="test_no_name_column",
            url_path="not-a-real-endpoint",
            default_params={},
            header_mappings={"player_id": "player_id"},  # no `name` target
            identity_columns=("player_id",),
        )

        mock_response = MagicMock()
        mock_response.text = '"player_id"\n660271\n592450\n'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = LeaderboardHandler()
        df = handler.extract(minimal_config)

        assert list(df.columns) == ["player_id"]
        # No name-parser-added columns when there's no source `name`
        for col in ("name", "first_name", "last_name", "name_ascii", "slug"):
            assert col not in df.columns
        assert len(df) == 2

    @patch("savant_api_extractor.handlers.base_handler.requests.get")
    def test_extract_long_format_on_pitch_type(
        self,
        mock_get: MagicMock,
        leaderboard_fixtures: dict[str, str],
    ) -> None:
        """pitch_arsenal_stats is long on pitch_type — Ohtani has multiple rows."""
        from savant_api_extractor.leaderboards import pitch_arsenal_stats

        config = pitch_arsenal_stats.BATTER
        mock_response = MagicMock()
        mock_response.text = leaderboard_fixtures[config.name]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = LeaderboardHandler()
        df = handler.extract(config, year="2026")

        ohtani_rows = df[df["name"] == "Ohtani, Shohei"]
        # Ohtani faces multiple pitch types — long-format-on-pitch_type confirmed
        assert len(ohtani_rows) > 1
        assert set(ohtani_rows["pitch_type"].unique()).issubset(
            {"FF", "SI", "FC", "SL", "CU", "CH", "FS", "KC", "ST", "SV"}
        )
