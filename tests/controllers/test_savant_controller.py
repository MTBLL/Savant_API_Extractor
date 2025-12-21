from unittest.mock import MagicMock, patch

import pytest

from savant_api_extractor.controller.savant_controller import SavantController
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.query_params import (
    FLAG_COMPETITIVE,
    FLAG_NOT_BUNT,
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
from savant_api_extractor.utils.thresholds import (
    DEFAULT_MIN_PAS_BATTER,
    DEFAULT_MIN_PAS_PITCHER,
    SPRING_TRAINING_MIN_PAS_BATTER,
    ThresholdType,
)


@pytest.fixture()
def controller() -> SavantController:
    return SavantController(ThresholdType.DEFAULT)


def test_generate_query_params_batter_default(
    controller: SavantController,
) -> None:
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.BATTER,
        season="2025",
    )
    assert params["player_type"] == "batter"
    assert params[HF_GAME_TYPE] == "R"
    assert params[GROUP_BY] == GROUP_BY_NAME
    assert params[MIN_PLATE_APPEARANCES] == str(DEFAULT_MIN_PAS_BATTER)
    assert params[SORT_COLUMN] == SORT_COL_XWOBA
    assert params[SORT_ORDER] == SORT_ORDER_DESC
    assert params[HF_FLAG] == f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|"
    assert params[HF_SEASON] == "2025"


def test_generate_query_params_pitcher_default(
    controller: SavantController,
) -> None:
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.PITCHER,
        season="2025",
    )
    assert params["player_type"] == "pitcher"
    assert params[HF_GAME_TYPE] == "R"
    assert params[GROUP_BY] == GROUP_BY_NAME
    assert params[MIN_PLATE_APPEARANCES] == str(DEFAULT_MIN_PAS_PITCHER)
    assert params[SORT_COLUMN] == SORT_COL_XWOBA
    assert params[SORT_ORDER] == SORT_ORDER_ASC
    assert params[HF_FLAG] == f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|"
    assert params[HF_SEASON] == "2025"


def test_generate_query_params_batter_spring_training(
    controller: SavantController,
) -> None:
    controller.threshold_type = ThresholdType.SPRING_TRAINING
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.BATTER,
        season="2025",
    )
    assert params["player_type"] == "batter"
    assert params[HF_GAME_TYPE] == "S"
    assert params[GROUP_BY] == GROUP_BY_NAME
    assert params[MIN_PLATE_APPEARANCES] == str(SPRING_TRAINING_MIN_PAS_BATTER)
    assert params[SORT_COLUMN] == SORT_COL_XWOBA
    assert params[SORT_ORDER] == SORT_ORDER_DESC
    assert params[HF_FLAG] == f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|"
    assert params[HF_SEASON] == "2025"


def test_controller_extract_batter(
    controller: SavantController,
    batters_fixture: str,
) -> None:
    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = batters_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = controller.extract(
            player_type=ExtractionType.BATTER,
            season="2025",
        )

    assert not df.empty
    assert "name" in df.columns
    assert "player_id" in df.columns


def test_controller_extract_pitcher(
    controller: SavantController,
    pitchers_fixture: str,
) -> None:
    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = pitchers_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = controller.extract(
            player_type=ExtractionType.PITCHER,
            season="2025",
        )

    assert not df.empty
    assert "name" in df.columns
    assert "player_id" in df.columns


def test_controller_extract_all_expect_error(
    controller: SavantController,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        controller.extract(
            player_type=ExtractionType.ALL,
            season="2025",
        )

        assert exc_info.value.args[0] == "Invalid player type"
