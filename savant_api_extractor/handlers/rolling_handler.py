"""Handler for the state-inlined rolling-windows leaderboard.

The Savant `/leaderboard/rolling` page is **state-inlined SSR**: the server
renders the HTML *and* embeds the full dataset as a JavaScript variable
assignment (`var rolling = {...};`) inside a `<script>` tag. The `csv=true`
shortcut that powers every other Savant leaderboard does NOT work here — it
returns the same HTML response. So this leaderboard gets its own handler:
fetch the HTML, regex-extract the `rolling` JS variable, and `json.loads` it.

If Savant ever migrates rolling to a real XHR/JSON API (consistent with how
their newer leaderboards work), that endpoint will show up in the browser
network tab — switch to it and delete the regex extraction below; it would
be strictly simpler than parsing inlined SSR state.
"""

from __future__ import annotations

import json
import re

import pandas as pd
import requests

from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.utils.name_parser import add_name_columns

# Standard sabermetric casing for the six rolling-window stats. Raw Savant
# columns are lowercase (`xwoba`); exported columns use the conventional
# capitalization (`xwOBA`).
_STAT_CASING = {
    "ba": "BA",
    "slg": "SLG",
    "woba": "wOBA",
    "xba": "xBA",
    "xslg": "xSLG",
    "xwoba": "xwOBA",
}


def _build_header_mappings() -> dict[str, str]:
    """Raw rolling column name -> normalized name.

    Identity columns pass through unchanged; each stat's triple is renamed
    `last_x_<stat>` -> `last_<STAT>`, `penultimate_x_<stat>` -> `prev_<STAT>`,
    `<stat>_delta` -> `<STAT>_delta`. Columns absent from the result are
    dropped from the output frame, mirroring `LeaderboardHandler`.
    """
    mappings: dict[str, str] = {
        "player_id": "player_id",
        "player_name": "name",
        "player_team_id": "player_team_id",
        "cat": "cat",
        "cat_bin": "cat_bin",
    }
    for raw, cased in _STAT_CASING.items():
        mappings[f"last_x_{raw}"] = f"last_{cased}"
        mappings[f"penultimate_x_{raw}"] = f"prev_{cased}"
        mappings[f"{raw}_delta"] = f"{cased}_delta"
    return mappings


HEADER_MAPPINGS = _build_header_mappings()

# Natural key of an output row.
IDENTITY_COLUMNS = ("player_id", "cat", "cat_bin")

# The `var rolling = {...};` assignment, bounded by the trailing `;` and the
# next `var ` / `</script>`. If Savant changes `var` to `let`/`const`, drops
# the semicolon, or renames the variable, this stops matching — surfaced
# loudly by `_parse_rolling_blob` raising, and pinned by a fixture test.
_ROLLING_PATTERN = re.compile(
    r"var\s+rolling\s*=\s*(\{.*?\});\s*(?=var |</script>)", re.DOTALL
)


class RollingHandler(BaseHandler):
    """Fetches and parses the state-inlined `/leaderboard/rolling` page."""

    ROLLING_URL = "https://baseballsavant.mlb.com/leaderboard/rolling"

    def __init__(self) -> None:
        super().__init__("RollingHandler")

    def extract(self) -> pd.DataFrame:
        """Fetch the rolling page, parse the inlined blob, return long-format.

        The `rolling` JS variable is an object of 6 keys
        (`{Batter,Pitcher} x {50,100,250}`). Every row already carries `cat`
        and `cat_bin`, so flattening is a plain list-extend across the keys —
        no identity columns need to be derived from the dict key.

        Returns:
            One long-format DataFrame, one row per `(player_id, cat, cat_bin)`.
            Columns are the `HEADER_MAPPINGS` targets plus the name-parser
            additions (`first_name`, `last_name`, `name_ascii`, `slug`). An
            all-empty blob yields an empty (column-less) DataFrame rather than
            raising.
        """
        self.logger.info("Extracting rolling-windows leaderboard")
        html = self._fetch_html()
        blob = self._parse_rolling_blob(html)

        rows: list[dict[str, object]] = []
        for category_rows in blob.values():
            rows.extend(category_rows)
        if rows:
            self.logger.info(
                f"Parsed {len(rows)} rolling rows across {len(blob)} categories"
            )
        else:
            # A valid blob whose 6 category lists are all empty — an
            # empty-result day, or an upstream filter / template change.
            # Surface it rather than writing a silent empty file.
            self.logger.warning(
                "Rolling blob parsed but all categories were empty"
            )

        df = pd.DataFrame(rows)
        df = df.rename(columns=HEADER_MAPPINGS)
        mapped = set(HEADER_MAPPINGS.values())
        df = df[[col for col in df.columns if col in mapped]].copy()
        # `name` is in HEADER_MAPPINGS, so it is present whenever there are
        # rows. The guard mirrors LeaderboardHandler: an empty blob yields a
        # column-less frame, and add_name_columns would assert on it.
        if "name" in df.columns:
            df = add_name_columns(df)
        return df

    def _fetch_html(self) -> str:
        try:
            response = requests.get(self.ROLLING_URL, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching rolling leaderboard: {e}")
            raise
        return response.text

    @staticmethod
    def _parse_rolling_blob(html: str) -> dict[str, list[dict[str, object]]]:
        """Extract and parse the `var rolling = {...};` assignment.

        Raises:
            ValueError: if the `var rolling = {...};` pattern is not found —
                i.e. Savant changed the page template. Fails loud rather than
                silently returning an empty frame.
        """
        match = _ROLLING_PATTERN.search(html)
        if not match:
            raise ValueError(
                "var rolling = {...}; pattern not found — Savant template "
                "may have changed (let/const instead of var? renamed "
                "variable? migrated to an XHR endpoint?)"
            )
        blob: dict[str, list[dict[str, object]]] = json.loads(match.group(1))
        return blob
