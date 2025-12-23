"""Tests for name parsing utilities."""

import pandas as pd

from savant_api_extractor.utils.name_parser import add_name_columns


def test_add_name_columns_parses_and_normalizes() -> None:
    df = pd.DataFrame(
        {
            "name": [
                "Judge, Aaron",
                "Díaz, José",
                "Madonna",
                "Guerror Jr., Vlad",
                "Aston Martin",
            ]
        }
    )

    result = add_name_columns(df)

    assert list(result.columns) == [
        "name",
        "first_name",
        "last_name",
        "name_ascii",
        "slug",
    ]

    assert result.loc[0, "first_name"] == "Aaron"
    assert result.loc[0, "last_name"] == "Judge"
    assert result.loc[0, "name_ascii"] == "Aaron Judge"
    assert result.loc[0, "slug"] == "aaron-judge"

    assert result.loc[1, "first_name"] == "José"
    assert result.loc[1, "last_name"] == "Díaz"
    assert result.loc[1, "name_ascii"] == "Jose Diaz"
    assert result.loc[1, "slug"] == "jose-diaz"

    assert result.loc[2, "first_name"] == "Madonna"
    assert result.loc[2, "last_name"] == ""
    assert result.loc[2, "name_ascii"] == "Madonna"
    assert result.loc[2, "slug"] == "madonna"

    assert result.loc[3, "first_name"] == "Vlad"
    assert result.loc[3, "last_name"] == "Guerror Jr."
    assert result.loc[3, "name_ascii"] == "Vlad Guerror Jr."
    assert result.loc[3, "slug"] == "vlad-guerror-jr"

    assert result.loc[4, "first_name"] == "Aston"
    assert result.loc[4, "last_name"] == "Martin"
    assert result.loc[4, "name_ascii"] == "Aston Martin"
    assert result.loc[4, "slug"] == "aston-martin"
