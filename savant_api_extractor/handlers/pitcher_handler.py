"""Handler for extracting pitcher statistics from Savant API."""

from typing import Any, Dict

import pandas as pd
import requests

from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.utils import PITCHER_HEADER_MAPPINGS


class PitcherHandler(BaseHandler):
    """Handler for extracting pitcher statistics."""

    def __init__(self) -> None:
        """Initialize the pitcher handler."""
        super().__init__("PitcherHandler")

    def extract(self, query_params: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract pitcher statistics from the Savant API.

        Args:
            query_params: Query parameters for the API request

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

            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching pitcher data: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing pitcher data: {e}")
            raise
