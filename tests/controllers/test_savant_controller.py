from unittest.mock import MagicMock, patch

import pytest

from savant_api_extractor.controller.savant_controller import SavantController
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.query_params import (
    BATTER_STANDS,
    FLAG_COMPETITIVE,
    FLAG_NOT_BUNT,
    GROUP_BY,
    GROUP_BY_NAME,
    HF_FLAG,
    HF_GAME_TYPE,
    HF_SEASON,
    MIN_PLATE_APPEARANCES,
    PITCHER_THROWS,
    SORT_COL_XWOBA,
    SORT_COLUMN,
    SORT_ORDER,
    SORT_ORDER_ASC,
    SORT_ORDER_DESC,
)
from savant_api_extractor.utils.thresholds import ThresholdType


@pytest.fixture()
def controller() -> SavantController:
    return SavantController(ThresholdType.DEFAULT)


def test_generate_query_params_batter_default(
    controller: SavantController,
) -> None:
    """The `all` extract is now emitted ungated — no min_pas in params.

    Previously this asserted `MIN_PLATE_APPEARANCES == DEFAULT_MIN_PAS_BATTER`,
    but threshold-gating moved out of the extract layer to fix the
    `R ∪ L ⊆ all` invariant violation: sub-threshold players were appearing
    in R/L (ungated) but not in `all` (gated), breaking downstream joins.
    """
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.BATTER,
        season="2025",
    )
    assert params["player_type"] == "batter"
    assert params[HF_GAME_TYPE] == "R"
    assert params[GROUP_BY] == GROUP_BY_NAME
    assert MIN_PLATE_APPEARANCES not in params
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
    assert MIN_PLATE_APPEARANCES not in params
    assert params[SORT_COLUMN] == SORT_COL_XWOBA
    assert params[SORT_ORDER] == SORT_ORDER_ASC
    assert params[HF_FLAG] == f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|"
    assert params[HF_SEASON] == "2025"


def test_generate_query_params_batter_spring_training(
    controller: SavantController,
) -> None:
    """Spring training threshold-type only flips game_type now (S vs R).

    The `threshold_type` setting still controls regular-season vs.
    spring-training, but no longer injects a min_pas filter.
    """
    controller.threshold_type = ThresholdType.SPRING_TRAINING
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.BATTER,
        season="2025",
    )
    assert params["player_type"] == "batter"
    assert params[HF_GAME_TYPE] == "S"
    assert params[GROUP_BY] == GROUP_BY_NAME
    assert MIN_PLATE_APPEARANCES not in params
    assert params[SORT_COLUMN] == SORT_COL_XWOBA
    assert params[SORT_ORDER] == SORT_ORDER_DESC
    assert params[HF_FLAG] == f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|"
    assert params[HF_SEASON] == "2025"


def test_controller_extract_batter(
    controller: SavantController,
    batters_all_fixture: str,
) -> None:
    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = batters_all_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = controller.extract(
            player_type=ExtractionType.BATTER,
            season="2026",
        )

    assert not df.empty
    assert "name" in df.columns
    assert "player_id" in df.columns
    assert (df["opp_hand"] == "all").all()


def test_controller_extract_pitcher(
    controller: SavantController,
    pitchers_all_fixture: str,
) -> None:
    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = pitchers_all_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = controller.extract(
            player_type=ExtractionType.PITCHER,
            season="2026",
        )

    assert not df.empty
    assert "name" in df.columns
    assert "player_id" in df.columns
    assert (df["opp_hand"] == "all").all()


def test_controller_extract_all_expect_error(
    controller: SavantController,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        controller.extract(
            player_type=ExtractionType.ALL,
            season="2025",
        )

        assert exc_info.value.args[0] == "Invalid player type"


def test_generate_query_params_batter_vs_rhp_drops_min_pas(
    controller: SavantController,
) -> None:
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.BATTER,
        season="2025",
        opp_hand="R",
    )
    assert params[PITCHER_THROWS] == "R"
    assert MIN_PLATE_APPEARANCES not in params
    assert BATTER_STANDS not in params


def test_generate_query_params_batter_vs_lhp_drops_min_pas(
    controller: SavantController,
) -> None:
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.BATTER,
        season="2025",
        opp_hand="L",
    )
    assert params[PITCHER_THROWS] == "L"
    assert MIN_PLATE_APPEARANCES not in params


def test_generate_query_params_pitcher_vs_rhb_uses_batter_stands(
    controller: SavantController,
) -> None:
    params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
        player_type=ExtractionType.PITCHER,
        season="2025",
        opp_hand="R",
    )
    assert params[BATTER_STANDS] == "R"
    assert MIN_PLATE_APPEARANCES not in params
    assert PITCHER_THROWS not in params


def test_generate_query_params_unknown_opp_hand_raises(
    controller: SavantController,
) -> None:
    with pytest.raises(ValueError):
        controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
            player_type=ExtractionType.BATTER,
            season="2025",
            opp_hand="S",
        )


def test_generate_query_params_no_min_pas_in_any_split(
    controller: SavantController,
) -> None:
    """Regression: no opp_hand split should inject `min_pas`.

    Threshold-gating the `all` split while leaving R/L ungated previously
    produced sub-threshold players appearing in R/L without an `all` row
    (71 players in 2025), breaking downstream joins. Post-fix, every split
    is emitted ungated so the invariant `set(R) ∪ set(L) ⊆ set(all)` holds
    by construction.
    """
    for opp_hand in ("all", "R", "L"):
        for player_type in (ExtractionType.BATTER, ExtractionType.PITCHER):
            params = controller._generate_query_params(  # pyright: ignore[reportPrivateUsage]
                player_type=player_type,
                season="2025",
                opp_hand=opp_hand,
            )
            assert MIN_PLATE_APPEARANCES not in params, (
                f"min_pas leaked into params for player_type={player_type}, "
                f"opp_hand={opp_hand}"
            )


def test_controller_extract_tags_opp_hand(
    controller: SavantController,
    batters_vs_R_fixture: str,
) -> None:
    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = batters_vs_R_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = controller.extract(
            player_type=ExtractionType.BATTER,
            season="2026",
            opp_hand="R",
        )

    assert "opp_hand" in df.columns
    assert (df["opp_hand"] == "R").all()
