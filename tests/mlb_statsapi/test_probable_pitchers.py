"""Tests for the MLB StatsAPI probable-pitchers fetcher.

Strategy: the happy path uses a captured fixture (2025-09-15, a fixed
historical date so the data doesn't drift). Edge cases (TBD pitcher,
empty schedule) use small synthetic payloads so they exercise the parser
without depending on a particular date's data.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from savant_api_extractor.mlb_statsapi import fetch_probable_pitchers
from savant_api_extractor.mlb_statsapi.probable_pitchers import (
    _parse_schedule_payload,
)


@pytest.fixture
def schedule_payload() -> dict:
    """Captured StatsAPI response for 2025-09-15 (9 games, all Final)."""
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "statsapi_schedule_response.json"
    )
    return json.loads(path.read_text())


def _build_mock_response(payload: dict) -> MagicMock:
    r = MagicMock()
    r.json.return_value = payload
    r.raise_for_status = MagicMock()
    return r


def test_fetch_returns_one_row_per_game(schedule_payload: dict) -> None:
    """The captured 2025-09-15 fixture has 9 games — output has 9 rows."""
    with patch(
        "savant_api_extractor.mlb_statsapi.probable_pitchers.requests.get",
        return_value=_build_mock_response(schedule_payload),
    ):
        rows = fetch_probable_pitchers("2025-09-15")
    assert len(rows) == 9


def test_fetch_row_shape_matches_contract(schedule_payload: dict) -> None:
    """Every row exposes the keys the ticket spec calls out."""
    with patch(
        "savant_api_extractor.mlb_statsapi.probable_pitchers.requests.get",
        return_value=_build_mock_response(schedule_payload),
    ):
        rows = fetch_probable_pitchers("2025-09-15")

    expected_keys = {
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
    for row in rows:
        assert set(row.keys()) == expected_keys


def test_fetch_known_matchup_strider_at_was(schedule_payload: dict) -> None:
    """Spot-check a known matchup from the fixture (anchored on Strider)."""
    with patch(
        "savant_api_extractor.mlb_statsapi.probable_pitchers.requests.get",
        return_value=_build_mock_response(schedule_payload),
    ):
        rows = fetch_probable_pitchers("2025-09-15")

    strider_game = next(
        r for r in rows if r["away_probable_name"] == "Spencer Strider"
    )
    assert strider_game["away_team_code"] == "atl"
    assert strider_game["away_team_name"] == "Atlanta Braves"
    assert strider_game["away_probable_id"] == 675911
    assert strider_game["home_team_code"] == "was"
    assert strider_game["home_probable_name"] == "Mitchell Parker"
    assert strider_game["gameState"] == "Final"


def test_fetch_passes_date_to_statsapi(schedule_payload: dict) -> None:
    """The date argument flows through to the StatsAPI request params."""
    with patch(
        "savant_api_extractor.mlb_statsapi.probable_pitchers.requests.get",
        return_value=_build_mock_response(schedule_payload),
    ) as mock_get:
        fetch_probable_pitchers("2025-09-15")

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["sportId"] == 1
    assert kwargs["params"]["date"] == "2025-09-15"
    assert "probablePitcher" in kwargs["params"]["hydrate"]


def test_fetch_accepts_date_object(schedule_payload: dict) -> None:
    """`datetime.date` argument is converted to ISO string before the call."""
    with patch(
        "savant_api_extractor.mlb_statsapi.probable_pitchers.requests.get",
        return_value=_build_mock_response(schedule_payload),
    ) as mock_get:
        fetch_probable_pitchers(date(2025, 9, 15))

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["date"] == "2025-09-15"


def test_parser_handles_tbd_pitcher() -> None:
    """When `probablePitcher` is missing, the row's *_probable_* fields are None."""
    synthetic = {
        "dates": [
            {
                "games": [
                    {
                        "gamePk": 999001,
                        "gameDate": "2026-04-15T23:10:00Z",
                        "status": {"abstractGameState": "Preview"},
                        "teams": {
                            "away": {
                                "team": {
                                    "id": 147,
                                    "name": "New York Yankees",
                                    "teamCode": "nya",
                                },
                                # probablePitcher omitted entirely
                            },
                            "home": {
                                "team": {
                                    "id": 119,
                                    "name": "Los Angeles Dodgers",
                                    "teamCode": "lan",
                                },
                                "probablePitcher": None,  # explicit null
                            },
                        },
                    }
                ]
            }
        ]
    }

    rows = _parse_schedule_payload(synthetic)
    assert len(rows) == 1
    row = rows[0]
    assert row["away_probable_id"] is None
    assert row["away_probable_name"] is None
    assert row["home_probable_id"] is None
    assert row["home_probable_name"] is None
    # Team metadata is still present
    assert row["away_team_code"] == "nya"
    assert row["home_team_code"] == "lan"
    assert row["gameState"] == "Preview"


def test_parser_handles_no_games_scheduled() -> None:
    """All-Star break / off-days return an empty list."""
    assert _parse_schedule_payload({"dates": []}) == []
    assert _parse_schedule_payload({"dates": [{"games": []}]}) == []
    # Missing `dates` key entirely (defensive)
    assert _parse_schedule_payload({}) == []


def test_fetch_propagates_http_errors() -> None:
    """4xx/5xx from StatsAPI surfaces as `requests.exceptions.HTTPError`."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("500 Internal Server Error")
    )

    with patch(
        "savant_api_extractor.mlb_statsapi.probable_pitchers.requests.get",
        return_value=mock_response,
    ):
        with pytest.raises(requests.exceptions.HTTPError):
            fetch_probable_pitchers("2025-09-15")


def test_fetch_propagates_connection_errors() -> None:
    """Network errors propagate as `requests.exceptions.ConnectionError`."""
    with patch(
        "savant_api_extractor.mlb_statsapi.probable_pitchers.requests.get",
        side_effect=requests.exceptions.ConnectionError("dns failure"),
    ):
        with pytest.raises(requests.exceptions.ConnectionError):
            fetch_probable_pitchers("2025-09-15")
