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

Each file contains a JSON array of player stat objects. Each player contributes
up to three rows per file — one row per handedness split. See
[Handedness Splits](#handedness-splits-opp_hand) below.

## Downstream Schema Notes

Downstream consumers should treat each row as role-specific, handedness-split
player-season data. The unique key for a row is the tuple
`(player_id, player_type, opp_hand)` plus season context. Do not use
`player_id` alone — two-way players appear in both output files, and every
player now contributes multiple rows for handedness splits.

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
  "opp_hand": "all",
  "hardhit_pct": 50.72463768115942,
  "hardhit_pct_pct_rnk": 86.4,
  "barrels_per_bbe_pct": 21.73913043478261,
  "barrels_per_bbe_pct_pct_rnk": 97.6,
  "barrels_per_pa_pct": 12.93103448275862,
  "barrels_per_pa_pct_pct_rnk": 96.9,
  "barrels_total": 15,
  "barrels_total_pct_rnk": 98.6
}
```

### Role Indicator

All exported rows include `player_type`:

- Batter rows use `"batter"`.
- Pitcher rows use `"pitcher"`.

This field is present even though batters and pitchers are written to separate
files. It exists so downstream systems that merge files can preserve separate
hitting and pitching stat lines for players such as Shohei Ohtani.

### Handedness Splits (`opp_hand`)

Each extraction produces up to three rows per player describing performance
against opposing handedness. The `opp_hand` column tags each row:

| `opp_hand` | Batter row meaning              | Pitcher row meaning             |
|------------|---------------------------------|---------------------------------|
| `"all"`    | Season totals (threshold-gated) | Season totals (threshold-gated) |
| `"R"`      | Stats vs right-handed pitchers  | Stats vs right-handed batters   |
| `"L"`      | Stats vs left-handed pitchers   | Stats vs left-handed batters    |

Behavior notes:

- **Threshold policy.** The `min_pas` threshold (`ThresholdType` in
  `savant_api_extractor.utils.thresholds`) is applied **only to `"all"` rows**.
  Split rows (`"R"`/`"L"`) are emitted with no minimum-PA gating so the dataset
  retains long-tail platoon-only players. Consumers that need a minimum sample
  for splits should filter downstream on `pa` (or equivalent counting stat).
- **Sparsity.** A player who never faced an opposing-side pitcher of a given
  handedness does not appear in that split — the row is simply absent rather
  than null-filled.
- **Server-side filter.** Splits are produced by querying the Savant CSV
  endpoint with `pitcher_throws=R|L` (for batters) or `batter_stands=R|L` (for
  pitchers). The schema returned by the API is identical across splits; only
  the underlying event set differs. No row appears in more than one split.
- **API load.** A full `all` extraction now issues six HTTP calls (three splits
  × two player types) instead of two. Each call takes a few seconds.

### Barrel and Hard-Hit Metrics

Both batter and pitcher exports include these contact-quality fields:

- `hardhit_pct`
- `barrels_per_bbe_pct`
- `barrels_per_pa_pct`
- `barrels_total`

Percentage fields are exported on Baseball Savant's percentage scale, not as
fractions. For example, `35.0` means 35%.

### Percentile Ranks

Each numeric stat field also gets a sibling percentile-rank field named
`<stat>_pct_rnk`. For example, `hardhit_pct` gets `hardhit_pct_pct_rnk`.

Percentile ranks are calculated **within-cohort**, meaning ranks are scoped to
the combination of role *and* handedness split:

- Batter `"all"` ranks compare only against other batter `"all"` rows.
- Batter `"R"` ranks compare only against other batter `"R"` rows.
- Batter `"L"` ranks compare only against other batter `"L"` rows.
- Pitcher cohorts are scoped analogously.

Because split rows are emitted without a `min_pas` threshold, split-cohort
percentile ranks include thin-sample players. Treat split percentile ranks as
indicative rather than authoritative until you filter on a meaningful PA
threshold downstream.

Identifier and metadata fields do not get percentile ranks. Excluded fields
are:

- `player_id`
- `name`
- `first_name`
- `last_name`
- `name_ascii`
- `slug`
- `player_type`
- `opp_hand`

Percentile ranks use pandas average-tie percentile ranking, scaled from 0 to 100
and rounded to one decimal place, based on the raw stat distribution. A higher
stat value receives a higher percentile rank. Ranks are not direction-adjusted
for whether a higher value is better for player evaluation.
