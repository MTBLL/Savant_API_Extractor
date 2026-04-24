"""Tests for percentile-rank utilities."""

import pandas as pd
import pytest

from savant_api_extractor.utils.percentile_ranks import add_percentile_rank_columns


def test_add_percentile_rank_columns_ranks_numeric_stats() -> None:
    df = pd.DataFrame(
        {
            "player_id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "player_type": ["batter", "batter", "batter"],
            "hardhit_pct": [10.0, 20.0, 20.0],
            "barrels_total": [3, 1, 2],
            "notes": ["low", "high", "high"],
        }
    )

    result = add_percentile_rank_columns(df)

    assert "player_id_pct_rnk" not in result.columns
    assert "name_pct_rnk" not in result.columns
    assert "player_type_pct_rnk" not in result.columns
    assert "notes_pct_rnk" not in result.columns
    assert result["hardhit_pct_pct_rnk"].to_list() == pytest.approx(
        [33.3, 83.3, 83.3]
    )
    assert result["barrels_total_pct_rnk"].to_list() == pytest.approx(
        [100.0, 33.3, 66.7]
    )


def test_add_percentile_rank_columns_preserves_original_values() -> None:
    df = pd.DataFrame(
        {
            "player_id": [1, 2],
            "name": ["A", "B"],
            "player_type": ["pitcher", "pitcher"],
            "xwOBA": [0.300, 0.250],
        }
    )

    result = add_percentile_rank_columns(df)

    assert result["xwOBA"].to_list() == [0.300, 0.250]
    assert result["xwOBA_pct_rnk"].to_list() == pytest.approx([100.0, 50.0])


def test_add_percentile_rank_columns_rejects_rank_column_collision() -> None:
    df = pd.DataFrame(
        {
            "player_id": [1, 2],
            "name": ["A", "B"],
            "player_type": ["batter", "batter"],
            "hardhit_pct": [10.0, 20.0],
            "hardhit_pct_pct_rnk": [50.0, 100.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="Percentile rank column already exists: hardhit_pct_pct_rnk",
    ):
        add_percentile_rank_columns(df)
