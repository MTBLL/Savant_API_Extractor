"""Generic puller for the `/leaderboard/{slug}?csv=true` endpoint family.

Unlike `BatterHandler` / `PitcherHandler` which target the single
`statcast_search` endpoint with bespoke query construction, this handler is
parameterized over a `LeaderboardConfig` describing any Savant leaderboard.
One handler instance serves all configured leaderboards.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.leaderboards._config import LeaderboardConfig
from savant_api_extractor.utils.name_parser import add_name_columns


class LeaderboardHandler(BaseHandler):
    """Pulls and normalizes a Savant leaderboard CSV per `LeaderboardConfig`."""

    LEADERBOARD_BASE = "https://baseballsavant.mlb.com/leaderboard/"

    def __init__(self) -> None:
        super().__init__("LeaderboardHandler")

    def extract(
        self,
        config: LeaderboardConfig,
        **overrides: Any,
    ) -> pd.DataFrame:
        """Pull this leaderboard, rename columns per config, return the frame.

        Args:
            config: The leaderboard endpoint description.
            **overrides: Per-call query-parameter overrides (e.g., `year=2026`).
                Merged on top of `config.default_params`. `csv=true` is always
                appended automatically.

        Returns:
            DataFrame with only the columns listed in `config.header_mappings`
            (renamed to their target names). When a `name` column is present
            after renaming, `add_name_columns` is applied to populate
            `first_name`, `last_name`, `name_ascii`, and `slug`.
        """
        params: dict[str, Any] = {
            **dict(config.default_params),
            **overrides,
            "csv": "true",
        }
        url = f"{self.LEADERBOARD_BASE}{config.url_path}"
        self.logger.info(f"Extracting leaderboard {config.name}")

        try:
            df = super().get_dataframe(params, url=url)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching leaderboard {config.name}: {e}")
            raise

        self.logger.info(
            f"Retrieved {len(df)} rows for leaderboard {config.name}"
        )

        # Rename columns and drop anything not in the mapping
        df = df.rename(columns=dict(config.header_mappings))
        mapped_columns = set(config.header_mappings.values())
        df = df[[col for col in df.columns if col in mapped_columns]].copy()

        # If a `name` column exists, parse it into first/last/ascii/slug.
        # Every ETL-tier leaderboard maps either `last_name, first_name` or
        # `player` to `name`, so this branch is taken in practice for all.
        if "name" in df.columns:
            df = add_name_columns(df)

        return df
