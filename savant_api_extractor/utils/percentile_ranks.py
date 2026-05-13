"""Utilities for adding role-local percentile ranks to extracted stats."""

from collections.abc import Iterable

import pandas as pd

PERCENTILE_RANK_SUFFIX = "_pct_rnk"

NON_STAT_COLUMNS = frozenset(
    {
        "player_id",
        "name",
        "first_name",
        "last_name",
        "name_ascii",
        "slug",
        "player_type",
        "opp_hand",
    }
)


def _percentile_rank(series: pd.Series) -> pd.Series:
    numeric_series = pd.to_numeric(series, errors="coerce")
    return (numeric_series.rank(method="average", pct=True) * 100).round(1)


def _stat_columns(
    df: pd.DataFrame,
    excluded_columns: Iterable[str],
) -> list[str]:
    excluded = set(excluded_columns)
    stat_columns = []

    for column in df.columns:
        if column in excluded or column.endswith(PERCENTILE_RANK_SUFFIX):
            continue

        numeric_values = pd.to_numeric(df[column], errors="coerce")
        if numeric_values.notna().any():
            stat_columns.append(column)

    return stat_columns


def add_percentile_rank_columns(
    df: pd.DataFrame,
    excluded_columns: Iterable[str] = NON_STAT_COLUMNS,
) -> pd.DataFrame:
    """Add a percentile-rank field for each numeric stat column.

    Ranks are calculated within the provided DataFrame. Callers should
    pre-filter to the cohort they want to rank against (e.g., role-specific
    rows, or a fantasy-relevant subset of rostered players) before calling
    this function. The extractor itself no longer applies percentile ranks
    at extract time — this utility exists for downstream consumers to apply
    against their own cohort.
    """
    ranked_df = df.copy()

    for stat_column in _stat_columns(ranked_df, excluded_columns):
        rank_column = f"{stat_column}{PERCENTILE_RANK_SUFFIX}"
        if rank_column in ranked_df.columns:
            raise ValueError(f"Percentile rank column already exists: {rank_column}")

        insert_index = ranked_df.columns.to_list().index(stat_column) + 1
        ranked_df.insert(
            insert_index, rank_column, _percentile_rank(ranked_df[stat_column])
        )

    return ranked_df
