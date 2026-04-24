# Savant API Extractor
[![codecov](https://codecov.io/gh/MTBLL/Savant_API_Extractor/graph/badge.svg?token=B63QRXrOeQ)](https://codecov.io/gh/MTBLL/Savant_API_Extractor)
![Mypy](https://github.com/MTBLL/Savant_API_Extractor/actions/workflows/mypy.yml/badge.svg)

## Description
This app pulls in the CSV api endpoint for the Baseball Savant statcast search.
The base url for the search tool is https://baseballsavant.mlb.com/statcast_search/csv? with all the available stats being pulled in for all the players.

This endpoint does not show other leaderboard stats such as Hot Stove Tracker, or rolling windows.

## Usage

Run the extractor with `uv run`:

```bash
uv run savant_api_extractor
```

When `--season` is omitted, the extractor uses the current calendar year. To pin
an extraction to a specific season, pass it explicitly:

```bash
uv run savant_api_extractor --season 2025
```

## Output Files

The default `all` extraction writes separate JSON files for batters and pitchers:

- `savant_batters_YYYY_MM_DD_HHMM.json`
- `savant_pitchers_YYYY_MM_DD_HHMM.json`

Each file contains a JSON array of player stat objects.

## Downstream Schema Notes

Downstream consumers should treat each row as role-specific player-season data.
Use `player_id`, `player_type`, and season context together when loading records.
Do not use `player_id` alone as a unique key because two-way players can appear in
both output files.

Rows do not currently include a `season` field. Consumers should persist the
season passed to the extractor, or the default current year when `--season` is
omitted, as job metadata during ingestion.

Example:

```json
{
  "player_id": 660271,
  "name": "Ohtani, Shohei",
  "first_name": "Shohei",
  "last_name": "Ohtani",
  "name_ascii": "Shohei Ohtani",
  "slug": "shohei-ohtani",
  "player_type": "batter",
  "hardhit_pct": 50.0,
  "barrels_per_bbe_pct": 22.727272727272727,
  "barrels_per_pa_pct": 13.513513513513514,
  "barrels_total": 15
}
```

### Role Indicator

All exported rows include `player_type`:

- Batter rows use `"batter"`.
- Pitcher rows use `"pitcher"`.

This field is present even though batters and pitchers are written to separate
files. It exists so downstream systems that merge files can preserve separate
hitting and pitching stat lines for players such as Shohei Ohtani.

### Barrel and Hard-Hit Metrics

Both batter and pitcher exports include these contact-quality fields:

- `hardhit_pct`
- `barrels_per_bbe_pct`
- `barrels_per_pa_pct`
- `barrels_total`

Percentage fields are exported on Baseball Savant's percentage scale, not as
fractions. For example, `35.0` means 35%.
