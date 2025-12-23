"""Controller for managing data extraction from Savant API."""

import pandas as pd

from savant_api_extractor.handlers.batter_handler import BatterHandler
from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.handlers.pitcher_handler import PitcherHandler
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.logger import Logger
from savant_api_extractor.utils.query_params import (
    FLAG_COMPETITIVE,
    FLAG_NOT_BUNT,
    GAME_TYPE_REGULAR,
    GAME_TYPE_SPRING_TRAINING,
    GROUP_BY,
    GROUP_BY_NAME,
    HF_FLAG,
    HF_GAME_TYPE,
    HF_SEASON,
    MIN_PLATE_APPEARANCES,
    SORT_COL_XWOBA,
    SORT_COLUMN,
    SORT_ORDER,
    SORT_ORDER_ASC,
    SORT_ORDER_DESC,
)
from savant_api_extractor.utils.thresholds import ThresholdType, get_min_pas


class SavantController:
    """Controller that interfaces with handlers to extract data."""

    def __init__(self, threshold_type: ThresholdType) -> None:
        """Initialize the controller with handlers."""
        self.logger: Logger = Logger(f"{__name__}.SavantController")
        self.batter_handler: BatterHandler = BatterHandler()
        self.pitcher_handler: PitcherHandler = PitcherHandler()
        self.logger.info("Controller initialized")
        self.threshold_type: ThresholdType = threshold_type

    def _generate_query_params(
        self,
        player_type: ExtractionType,
        season: str,
    ) -> dict[str, str]:
        """
        Generate query parameters based on options.

        Args:
            player_type: "batters" or "pitchers"
            threshold_type: Threshold type for minimum plate appearances
            season: Season year (e.g., "2025").
            If None, uses current year logic.

        Returns:
            Dictionary of query parameters
        """
        min_pas = get_min_pas(self.threshold_type, player_type)

        player_type_param = {
            ExtractionType.BATTER: "batter",
            ExtractionType.PITCHER: "pitcher",
        }.get(player_type)

        assert player_type_param is not None, f"Unsupported player type: {player_type}"

        params: dict[str, str] = {
            "player_type": player_type_param,
            HF_GAME_TYPE: (
                GAME_TYPE_SPRING_TRAINING
                if self.threshold_type == ThresholdType.SPRING_TRAINING
                else GAME_TYPE_REGULAR
            ),
            GROUP_BY: GROUP_BY_NAME,
            MIN_PLATE_APPEARANCES: min_pas,
            SORT_COLUMN: SORT_COL_XWOBA,
            SORT_ORDER: (
                SORT_ORDER_ASC
                if player_type == ExtractionType.PITCHER
                else SORT_ORDER_DESC
            ),
            HF_FLAG: f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|",
            HF_SEASON: season,
        }

        self.logger.debug(
            (
                f"Generated {player_type} query params with "
                f"threshold={self.threshold_type.value}, "
                f"min_pas={min_pas}"
            )
        )

        return params

    def extract(
        self,
        player_type: ExtractionType,
        season: str,
    ) -> pd.DataFrame:
        """
        Extract player statistics.

        Args:
            player_type: "batters" or "pitchers"
            threshold_type: Threshold type for minimum plate appearances
            season: Season year (e.g., "2025"). If None, uses current year logic.

        Returns:
            DataFrame with player statistics
        """
        handler: BaseHandler
        match player_type:
            case ExtractionType.BATTER:
                handler = self.batter_handler
            case ExtractionType.PITCHER:
                handler = self.pitcher_handler
            case _:
                raise ValueError(f"Unsupported player type: {player_type}")

        self.logger.info("Extracting player statistics")
        query_params = self._generate_query_params(player_type, season)
        return handler.extract(query_params)
