"""Tests for round-half-up export rounding."""

from __future__ import annotations

import math

import pandas as pd

from savant_api_extractor.utils.rounding import round_float_columns, round_half_up


class TestRoundHalfUp:
    def test_ties_round_up_not_to_even(self) -> None:
        # Built-in round() uses banker's rounding (round-half-to-even):
        # round(0.1245, 3) == 0.124, round(2.5) == 2. round_half_up sends
        # the 5 up unconditionally.
        assert round_half_up(0.1245) == 0.125
        assert round_half_up(0.1255) == 0.126
        assert round_half_up(2.5, places=0) == 3.0

    def test_ties_for_negatives_round_away_from_zero(self) -> None:
        # ROUND_HALF_UP = ties away from zero.
        assert round_half_up(-0.1245) == -0.125
        assert round_half_up(-2.5, places=0) == -3.0

    def test_non_tie_values_round_normally(self) -> None:
        # Real swing-take wire values (full float precision -> 3 decimals).
        assert round_half_up(3.730589042980745) == 3.731
        assert round_half_up(0.6915475716321668) == 0.692
        assert round_half_up(-8.346893561202931) == -8.347

    def test_nan_and_inf_pass_through(self) -> None:
        assert math.isnan(round_half_up(float("nan")))
        assert round_half_up(float("inf")) == float("inf")
        assert round_half_up(float("-inf")) == float("-inf")

    def test_already_short_values_unchanged(self) -> None:
        assert round_half_up(1.5) == 1.5
        assert round_half_up(0.0) == 0.0


class TestRoundFloatColumns:
    def test_only_float_columns_rounded(self) -> None:
        df = pd.DataFrame(
            {
                "player_id": [660271, 592450],  # int — untouched
                "year": [2026, 2026],  # int — untouched
                "runs_all": [3.730589, -8.346894],  # float — rounded
                "name": ["Ohtani, Shohei", "Judge, Aaron"],  # object — untouched
            }
        )
        out = round_float_columns(df)

        assert list(out["runs_all"]) == [3.731, -8.347]
        # int and object columns are byte-for-byte identical
        assert list(out["player_id"]) == [660271, 592450]
        assert out["player_id"].dtype == df["player_id"].dtype
        assert list(out["name"]) == ["Ohtani, Shohei", "Judge, Aaron"]

    def test_does_not_mutate_input(self) -> None:
        df = pd.DataFrame({"runs_all": [3.730589]})
        round_float_columns(df)
        assert df["runs_all"].iloc[0] == 3.730589  # original untouched

    def test_nan_preserved_in_float_column(self) -> None:
        df = pd.DataFrame({"runs_all": [3.730589, float("nan")]})
        out = round_float_columns(df)
        assert out["runs_all"].iloc[0] == 3.731
        assert math.isnan(out["runs_all"].iloc[1])
