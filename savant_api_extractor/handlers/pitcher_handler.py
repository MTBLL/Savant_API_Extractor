"""Handler for extracting pitcher statistics from Savant API."""

from typing import Any, Dict

import pandas as pd
import requests

from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.utils import PITCHER_HEADER_MAPPINGS
from savant_api_extractor.utils.name_parser import add_name_columns
from savant_api_extractor.utils.percentile_ranks import add_percentile_rank_columns


class PitcherHandler(BaseHandler):
    """Handler for extracting pitcher statistics."""

    def __init__(self) -> None:
        """Initialize the pitcher handler."""
        super().__init__("PitcherHandler")

    def extract(
        self,
        query_params: Dict[str, Any],
        opp_hand: str = "all",
    ) -> pd.DataFrame:
        """
        Extract pitcher statistics from the Savant API.

        Args:
            query_params: Query parameters for the API request
            opp_hand: Tag value for the opp_hand column ("all", "R", or "L").

        Returns:
            DataFrame with cleaned pitcher statistics
        """
        self.logger.info("Extracting pitcher statistics")

        try:
            df = super().get_dataframe(query_params)

            self.logger.info(f"Retrieved {len(df)} rows of pitcher data")

            # Clean headers: rename and filter to only mapped columns
            df = df.rename(columns=PITCHER_HEADER_MAPPINGS)
            # Keep only columns that exist in the mapping (after renaming)
            mapped_columns = set(PITCHER_HEADER_MAPPINGS.values())
            df = df[[col for col in df.columns if col in mapped_columns]]

            df = add_name_columns(df)
            slug_index = df.columns.to_list().index("slug")
            df.insert(slug_index + 1, "player_type", "pitcher")
            df.insert(slug_index + 2, "opp_hand", opp_hand)
            return add_percentile_rank_columns(df)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching pitcher data: {e}")
            raise
