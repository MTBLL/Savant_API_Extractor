"""Handler for the state-inlined birthday-index page.

The Savant `/birthday-index` page (Sarah Langs' Birthday Index) is
**state-inlined SSR** — the same family as the rolling-windows leaderboard.
The server renders the HTML and embeds the dataset as `const` JavaScript
variable assignments in a `<script>` tag; `?csv=true` returns the same HTML.

The "Birthday Index" is a Savant-computed stat: a player's wOBA on their
birthday vs. all other dates, sample-weighted by birthday PAs. It feeds
streaming-pitcher and bench/platoon start-sit decisions, so this is an
RT-fetch handler — the analytics app calls it on demand; it is NOT pulled
by the bulk runner.

Only **active** players are returned. The raw `birthdayData` array is ~90%
retired/historical players (the page's birthday data goes back to 1969);
`extract` filters to `is_player_active == 1` before mapping.

If Savant ever migrates this to a real XHR/JSON endpoint, switch to it and
drop the regex extraction below — it would be strictly simpler.
"""

from __future__ import annotations

import json
import re

import pandas as pd
import requests

from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.utils.name_parser import add_name_columns

# Raw `birthdayData` column -> normalized name. Columns absent from this
# mapping are dropped, mirroring LeaderboardHandler / RollingHandler. The raw
# page carries redundant duplicates (`player_name` == `name`, `id` ==
# `player_id`), `*_hidden` sort-helpers, a `dateString` display field, and
# the `is_player_*` flags (consumed by the active-player filter, not
# emitted) — all dropped by omission here.
HEADER_MAPPINGS: dict[str, str] = {
    "player_id": "player_id",
    "name": "name",
    "player_type": "player_type",
    "actual_birthday": "actual_birthday",
    "birth_day_noyear": "birth_day_noyear",
    "age": "age",
    "daysUntil": "daysUntil",
    "isBirthday": "isBirthday",
    "birthday_index": "birthday_index",
    "birthday_games": "birthday_games",
    "birthday_pa": "birthday_pa",
    "birthday_BA": "birthday_BA",
    "non_birthday_BA": "non_birthday_BA",
    "birthday_BA_diff": "birthday_BA_diff",
    "birthday_OPS": "birthday_OPS",
    "non_birthday_OPS": "non_birthday_OPS",
    "birthday_OPS_diff": "birthday_OPS_diff",
    "birthday_wOBA": "birthday_wOBA",
    "non_birthday_wOBA": "non_birthday_wOBA",
    "birthday_wOBA_diff": "birthday_wOBA_diff",
    "birthday_hits": "birthday_hits",
    "birthday_hit_1b": "birthday_hit_1b",
    "birthday_hit_2b": "birthday_hit_2b",
    "birthday_hit_3b": "birthday_hit_3b",
    "birthday_hit_hr": "birthday_hit_hr",
    "birthday_strikeout": "birthday_strikeout",
    "birthday_k_percent": "birthday_k_percent",
    "birthday_walk": "birthday_walk",
    "birthday_bb_percent": "birthday_bb_percent",
}

# Natural key of an output row.
IDENTITY_COLUMNS = ("player_id", "player_type")

# The `const birthdayData = [...];` assignment. Note `const` — the page uses
# `const`, not the `var` of the rolling leaderboard, so RollingHandler's
# pattern would not match. The `birthdayData` rows are flat objects (no
# nested arrays), so the first `];` non-greedily terminates the array.
_BIRTHDAY_PATTERN = re.compile(r"const\s+birthdayData\s*=\s*(\[.*?\]);", re.DOTALL)

_VALID_PLAYER_TYPES = ("batter", "pitcher")


class BirthdayIndexHandler(BaseHandler):
    """Fetches and parses the state-inlined `/birthday-index` page."""

    BIRTHDAY_INDEX_URL = "https://baseballsavant.mlb.com/birthday-index"

    def __init__(self) -> None:
        super().__init__("BirthdayIndexHandler")

    def extract(self, player_type: str = "batter") -> pd.DataFrame:
        """Fetch the birthday-index page, parse the inlined blob, return a frame.

        Args:
            player_type: "batter" or "pitcher" — selects which side's table
                the page renders (the `?type=` query parameter).

        Returns:
            One DataFrame, one row per **active** player. Columns are the
            `HEADER_MAPPINGS` targets plus the name-parser additions
            (`first_name`, `last_name`, `name_ascii`, `slug`). Only active
            players (`is_player_active == 1`) are kept — the raw page is ~90%
            retired/historical players. An all-inactive result yields an
            empty (column-less) DataFrame rather than raising.

        Raises:
            ValueError: if `player_type` is not "batter" or "pitcher", or if
                the `const birthdayData = [...];` pattern is not found.
        """
        if player_type not in _VALID_PLAYER_TYPES:
            raise ValueError(
                f"player_type must be one of {_VALID_PLAYER_TYPES}, "
                f"got {player_type!r}"
            )

        self.logger.info(f"Extracting birthday-index ({player_type})")
        html = self._fetch_html(player_type)
        blob = self._parse_birthday_blob(html)

        active = [row for row in blob if row.get("is_player_active") == 1]
        self.logger.info(
            f"birthday-index ({player_type}): {len(active)} active of "
            f"{len(blob)} rows"
        )

        df = pd.DataFrame(active)
        df = df.rename(columns=HEADER_MAPPINGS)
        mapped = set(HEADER_MAPPINGS.values())
        df = df[[col for col in df.columns if col in mapped]].copy()
        # `name` is in HEADER_MAPPINGS, so it is present whenever there are
        # active rows. The guard mirrors RollingHandler: an all-inactive
        # result yields a column-less frame, and add_name_columns would
        # assert on it.
        if "name" in df.columns:
            df = add_name_columns(df)
        return df

    def _fetch_html(self, player_type: str) -> str:
        try:
            response = requests.get(
                self.BIRTHDAY_INDEX_URL,
                params={"type": player_type},
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching birthday-index: {e}")
            raise
        return response.text

    @staticmethod
    def _parse_birthday_blob(html: str) -> list[dict[str, object]]:
        """Extract and parse the `const birthdayData = [...];` assignment.

        Raises:
            ValueError: if the `const birthdayData = [...];` pattern is not
                found — i.e. Savant changed the page template (`let`/`var`
                instead of `const`? renamed variable? migrated to an XHR
                endpoint?). Fails loud rather than silently returning empty.
        """
        match = _BIRTHDAY_PATTERN.search(html)
        if not match:
            raise ValueError(
                "const birthdayData = [...]; pattern not found — Savant "
                "template may have changed (let/var instead of const? "
                "renamed variable? migrated to an XHR endpoint?)"
            )
        blob: list[dict[str, object]] = json.loads(match.group(1))
        return blob
