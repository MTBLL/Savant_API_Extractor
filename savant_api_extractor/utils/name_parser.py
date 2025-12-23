"""Utilities for parsing player names."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


def _to_ascii(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _slugify(value: str) -> str:
    ascii_value = _to_ascii(value).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value)
    return slug.strip("-")


def _split_name(value: str) -> tuple[str, str]:
    if "," in value:
        last, first = value.split(",", 1)
        return first.strip(), last.strip()

    parts = value.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()

    return value.strip(), ""


def add_name_columns(df: pd.DataFrame, name_column: str = "name") -> pd.DataFrame:
    """
    Add parsed name columns to the DataFrame.

    Columns added:
      - first_name
      - last_name
      - name_ascii
      - slug
    """
    assert name_column in df.columns, f"Column '{name_column}' not found in DataFrame"

    name_series = df[name_column].fillna("")
    split_names = name_series.map(_split_name)
    df["first_name"] = split_names.map(lambda parts: parts[0])
    df["last_name"] = split_names.map(lambda parts: parts[1])

    full_name = df["first_name"].str.cat(df["last_name"], sep=" ").str.strip()
    df["name_ascii"] = full_name.map(_to_ascii)
    df["slug"] = full_name.map(_slugify)

    columns = df.columns.to_list()
    insert_after = columns.index(name_column) + 1
    new_columns = ["first_name", "last_name", "name_ascii", "slug"]
    remaining = [col for col in columns if col not in new_columns]
    ordered_columns = (
        remaining[:insert_after] + new_columns + remaining[insert_after:]
    )
    return df[ordered_columns]
