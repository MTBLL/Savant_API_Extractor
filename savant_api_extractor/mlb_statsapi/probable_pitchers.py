"""Probable pitchers from MLB StatsAPI — the canonical source.

The Savant `/probable-pitchers` page is a UI on top of this same StatsAPI
endpoint. Hitting StatsAPI directly avoids the HTML scrape and uses the
authoritative source.

Endpoint (public, no auth required):
    GET https://statsapi.mlb.com/api/v1/schedule
        ?sportId=1
        &date=YYYY-MM-DD
        &hydrate=probablePitcher,team,lineups

Use case: the analytics app calls `fetch_probable_pitchers(date)` when
rendering the daily slate. Not invoked by the bulk Savant runner.
"""

from __future__ import annotations

from datetime import date as _date_type
from typing import Any

import requests

from savant_api_extractor.utils.logger import Logger

STATSAPI_SCHEDULE_URL: str = "https://statsapi.mlb.com/api/v1/schedule"
HYDRATE_FIELDS: str = "probablePitcher,team,lineups"
SPORT_ID_MLB: int = 1
REQUEST_TIMEOUT_SECONDS: int = 15

_logger = Logger(__name__)


def fetch_probable_pitchers(date: str | _date_type) -> list[dict[str, Any]]:
    """Fetch probable pitchers for every game scheduled on `date`.

    Args:
        date: ISO date string ("2025-09-15") or `datetime.date`. Local
            calendar date — the StatsAPI does the timezone conversion for
            game scheduling.

    Returns:
        List of dicts, one per scheduled game on `date`. Each dict has the
        keys documented in the ticket (gamePk, gameDate, gameState, away_*,
        home_*). Probable-pitcher fields are `None` when no pitcher has been
        announced ("TBD") for that team. Returns `[]` if no games are
        scheduled on the date.

    Raises:
        requests.exceptions.RequestException: on network / HTTP errors.
            Callers wanting graceful degradation should catch and decide.
    """
    date_str = date if isinstance(date, str) else date.isoformat()

    _logger.info(f"Fetching probable pitchers for {date_str}")
    # All values cast to str so the dict is mono-typed — matches the
    # convention in SavantController._generate_query_params and keeps the
    # requests stub happy (mixing str + int values would infer dict[str, object]).
    params: dict[str, str] = {
        "sportId": str(SPORT_ID_MLB),
        "date": date_str,
        "hydrate": HYDRATE_FIELDS,
    }
    response = requests.get(
        STATSAPI_SCHEDULE_URL,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()

    return _parse_schedule_payload(payload)


def _parse_schedule_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Translate a raw StatsAPI schedule response into our row shape.

    Separated from the HTTP fetch so tests can exercise the parser against
    captured / synthetic fixtures without mocking the network layer.
    """
    dates = payload.get("dates") or []
    if not dates:
        return []

    games = dates[0].get("games") or []
    return [_game_to_row(g) for g in games]


def _game_to_row(game: dict[str, Any]) -> dict[str, Any]:
    """Project a single StatsAPI game record into our output dict shape."""
    away = game["teams"]["away"]
    home = game["teams"]["home"]
    away_pitcher = away.get("probablePitcher") or {}
    home_pitcher = home.get("probablePitcher") or {}

    return {
        "gamePk": game["gamePk"],
        "gameDate": game["gameDate"],
        "gameState": game["status"]["abstractGameState"],
        "away_team_code": away["team"].get("teamCode"),
        "away_team_name": away["team"].get("name"),
        "away_probable_id": away_pitcher.get("id"),
        "away_probable_name": away_pitcher.get("fullName"),
        "home_team_code": home["team"].get("teamCode"),
        "home_team_name": home["team"].get("name"),
        "home_probable_id": home_pitcher.get("id"),
        "home_probable_name": home_pitcher.get("fullName"),
    }
