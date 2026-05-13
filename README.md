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

A full `all` extraction writes **ten JSON files** to the output directory:

**Two handedness-split files** (from the `statcast_search` endpoint family):

- `savant_batters_YYYY_MM_DD_HHMM.json` — batter rows, up to 3 per player (one per `opp_hand`)
- `savant_pitchers_YYYY_MM_DD_HHMM.json` — pitcher rows, same shape

**Eight leaderboard files** (from the `/leaderboard/*?csv=true` endpoint family):

- `savant_statcast_batter_YYYY_MM_DD_HHMM.json` — contact quality (hit)
- `savant_statcast_pitcher_YYYY_MM_DD_HHMM.json` — contact quality (allowed)
- `savant_expected_statistics_pitcher_YYYY_MM_DD_HHMM.json` — x-stats (allowed) + xERA *(the batter variant is intentionally not pulled — its columns are already in the batter splits file)*
- `savant_home_runs_batter_YYYY_MM_DD_HHMM.json` — HR / xHR / park-adjusted (hit)
- `savant_home_runs_pitcher_YYYY_MM_DD_HHMM.json` — HR / xHR / park-adjusted (allowed)
- `savant_pitch_arsenal_stats_batter_YYYY_MM_DD_HHMM.json` — batter per-pitch outcomes (long on `pitch_type`)
- `savant_pitch_arsenal_stats_pitcher_YYYY_MM_DD_HHMM.json` — pitcher per-pitch outcomes (long on `pitch_type`)
- `savant_sprint_speed_YYYY_MM_DD_HHMM.json` — baserunning speed + bolts

Each file is a JSON array of row objects, joinable on `player_id`. See [Leaderboard extracts](#leaderboard-extracts) below for the data contract and `savant_api_extractor/leaderboards/SPECS.md` for live per-endpoint snapshots.

To skip the leaderboard pulls (splits only), construct the runner with `include_leaderboards=False`.

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

- **Threshold policy.** All three splits (`"all"`, `"R"`, `"L"`) are emitted
  **ungated** — no `min_pas` filter is applied at extract time. Cohort
  gating is a downstream concern and belongs in the analytics layer (filter
  by `pa` after loading into DuckDB, against your own rostered-player cohort
  rather than Savant's qualified pool). The `ThresholdType` enum still
  controls regular-season vs. spring-training game-type selection, but no
  longer injects a `min_pas` filter.
- **Structural invariant: `set(R) ∪ set(L) ⊆ set(all)`.** Every player who
  appears in a vs-RHP or vs-LHP split also has an overall row. This holds by
  construction because all three splits are emitted with the same gating
  policy (none). Downstream joins keyed on `(player_id, "all")` will not lose
  rows that appear in the platoon splits.
- **Sparsity.** A player who never faced an opposing-side pitcher of a given
  handedness does not appear in that split — the row is simply absent rather
  than null-filled.
- **Server-side filter.** Splits are produced by querying the Savant CSV
  endpoint with `pitcher_throws=R|L` (for batters) or `batter_stands=R|L` (for
  pitchers). The schema returned by the API is identical across splits; only
  the underlying event set differs. No row appears in more than one split.
- **API load.** A full `all` extraction now issues six HTTP calls (three splits
  × two player types) instead of two. Each call takes a few seconds.

### Leaderboard extracts

The eight `savant_{slug}_*.json` files are independent extracts of Savant's `/leaderboard/{slug}?csv=true` endpoints — different schemas, different identity keys, joinable on `player_id` downstream.

#### Per-endpoint contract

| Output file slug | Identity key | Predicts (6×6 H2H) |
|---|---|---|
| `statcast_batter` | `(player_id,)` | HR, SLG — max_ev, barrels, hard-hit |
| `statcast_pitcher` | `(player_id,)` | ERA, WHIP, K/9 — allowed contact quality |
| `expected_statistics_pitcher` | `(player_id, year)` | ERA, WHIP — **xERA**, xwOBA allowed (only Savant source of xERA) |
| `home_runs_batter` | `(player_id, year, hr_type)` | HR — xHR, park-adjusted variants |
| `home_runs_pitcher` | `(player_id, year, hr_type)` | (HR allowed — context only) |
| `pitch_arsenal_stats_batter` | `(player_id, pitch_type)` | matchup projection — batter vs pitch-type (long-format) |
| `pitch_arsenal_stats_pitcher` | `(player_id, pitch_type)` | matchup projection — pitcher arsenal (long-format) |
| `sprint_speed` | `(player_id,)` | SB — sprint_speed, bolts, hp_to_1b |

> The batter variant of `expected_statistics` is intentionally **not** ETL'd — every column it provided (PA, AVG, xAVG/xAVGdiff, SLG/xSLG/xSLGdiff, wOBA/xwOBA/wOBAdiff, BIP) is also returned by the `statcast_search` endpoint that feeds the `savant_batters_*.json` splits file. Pulling it would be redundant.

For full column lists, header mappings, and live snapshot samples, see [`savant_api_extractor/leaderboards/SPECS.md`](savant_api_extractor/leaderboards/SPECS.md).

#### Example DuckDB load

```sql
-- Load each role-relevant table. The "all" row of the batter splits is the
-- batter-side baseline; xwOBA / xSLG / xAVG / PA / AVG / wOBA / SLG / OBP all live there.
CREATE TABLE batters_splits         AS SELECT * FROM read_json_auto('savant_batters_*.json');
CREATE TABLE statcast_batter        AS SELECT * FROM read_json_auto('savant_statcast_batter_*.json');
CREATE TABLE sprint_speed           AS SELECT * FROM read_json_auto('savant_sprint_speed_*.json');
CREATE TABLE pitch_arsenal_batter   AS SELECT * FROM read_json_auto('savant_pitch_arsenal_stats_batter_*.json');

-- Compose a batter projection view joining the splits baseline + 3 leaderboards
CREATE VIEW batter_projection AS
SELECT
  b.player_id, b.name,
  b."xwOBA", b."xSLG", b."xAVG", b."PA", b."AVG",  -- from batters splits (opp_hand='all')
  s.max_ev, s.barrels_per_pa_pct,                  -- from statcast leaderboard
  sp.sprint_speed, sp.bolts,                       -- from sprint_speed leaderboard
  pa.pitch_type, pa."xwOBA" AS xwOBA_vs_pitch      -- from pitch_arsenal (long-format)
FROM batters_splits b
LEFT JOIN statcast_batter      s  ON b.player_id = s.player_id
LEFT JOIN sprint_speed         sp ON b.player_id = sp.player_id
LEFT JOIN pitch_arsenal_batter pa ON b.player_id = pa.player_id
WHERE b.opp_hand = 'all';
-- Each (player_id) row from batters_splits expands to N rows here, one per
-- pitch_type the batter has faced (because pitch_arsenal_batter is long-format).
```

#### Adding a new leaderboard

Each leaderboard is a single `LeaderboardConfig` dataclass declared in `savant_api_extractor/leaderboards/{slug}.py`. Adding a new one means: write the config (URL path, default params, header mappings, identity columns), append it to `ETL_TIER_CONFIGS` (or `RT_TIER_CONFIGS` — see below) in `leaderboards/__init__.py`, save a fixture CSV under `tests/fixtures/leaderboards/{name}.csv`, and the existing parameterized handler test picks it up.

### Realtime-fetch leaderboards (RT-tier)

Six additional leaderboards are configured but **not pulled by the bulk runner**. They live in `RT_TIER_CONFIGS` and are intended for the analytics app to call on demand — when viewing a specific matchup, fetch the probable pitcher's per-pitch arsenal, the batter's swing path, etc. The same `LeaderboardHandler` consumes them; only the cadence differs (per-request, not nightly).

| Slug | Use case |
|---|---|
| `pitch_arsenals` | Per-pitch avg velocity per pitcher (wide on pitch type) — archetype |
| `pitch_movement` | Per-pitch break vs league (long on pitch type) — K/9 & WHIP predictor |
| `active_spin` | Active-spin % per pitch type per pitcher (wide on pitch type) — K/9 archetype |
| `pitcher_arm_angles` | Release point / arm slot — release archetype |
| `bat_tracking_swing_path` | Batter swing diagnostics (bat speed, attack angle) |
| `batted_ball_batter` | Pull-air rate + GB/FB/LD/pull/oppo rates — HR drill-down |

#### Calling an RT config from an analytics app

```python
from savant_api_extractor.handlers import LeaderboardHandler
from savant_api_extractor.leaderboards import pitch_arsenals, pitch_movement

handler = LeaderboardHandler()

# Pull a pitcher's whole arsenal (one row per pitcher; pitch_arsenals is wide)
arsenals_df = handler.extract(pitch_arsenals.CONFIG, year="2026")
strider = arsenals_df[arsenals_df["player_id"] == 675911]
strider_ff_velo = strider["ff_avg_speed"].iloc[0]

# Pull every pitcher's movement profile (long-format on pitch_type)
movement_df = handler.extract(pitch_movement.CONFIG, year="2026")
strider_breakers = movement_df[
    (movement_df["player_id"] == 675911) & (movement_df["pitch_type"].isin(["SL", "CU"]))
]
```

#### Caching policy

This package is the **network layer only**. RT-tier responses are not cached by the handler — every `extract()` call hits Savant. Analytics-app callers should layer their own caching (per-request, per-day, etc.) appropriate to their query patterns. The handler is idempotent within a season, so a 1-day cache TTL is usually sufficient for these endpoints.

For full per-endpoint column lists, header mappings, and live snapshot samples, see [`savant_api_extractor/leaderboards/SPECS.md`](savant_api_extractor/leaderboards/SPECS.md) (Part II: RT-tier endpoints).

### Barrel and Hard-Hit Metrics

Both batter and pitcher exports include these contact-quality fields:

- `hardhit_pct`
- `barrels_per_bbe_pct`
- `barrels_per_pa_pct`
- `barrels_total`

Percentage fields are exported on Baseball Savant's percentage scale, not as
fractions. For example, `35.0` means 35%.

### Percentile Ranks (computed downstream, not at extract time)

The extractor emits **raw stat values only**. Percentile ranks are no longer
applied at extract time — they're only meaningful relative to the cohort
they're computed against, and the right cohort depends on the consumer:

- A fantasy analytics app should compute percentiles against its rostered
  player set (typically ~250 hitters / ~150 pitchers), not against Savant's
  full qualified cohort (~600 players).
- A scouting tool comparing prospects to league-wide benchmarks would want
  the opposite — ranks against the full Savant cohort.

Computing ranks at extract time would lock all downstream consumers to one
cohort definition. Cohort mismatch inverts the rank signal at the tails (a
90th-percentile fantasy hitter looks like a 75th-percentile MLB hitter, and
vice versa). So this extractor's job is now to produce raw values; consumers
compute their own ranks.

The `add_percentile_rank_columns` utility used in earlier versions of this
extractor remains exported for downstream use. Import and apply it after
filtering to your cohort of interest:

```python
import pandas as pd
from savant_api_extractor.utils.percentile_ranks import add_percentile_rank_columns

# Load the extractor output and filter to your fantasy cohort:
batters = pd.read_json("savant_batters_2025_10_01_1200.json")
overall = batters[batters["opp_hand"] == "all"]
rostered = overall[overall["player_id"].isin(my_fantasy_player_ids)]

# Then rank within that cohort:
ranked = add_percentile_rank_columns(rostered)
# Adds `<stat>_pct_rnk` columns for every numeric stat field.
```

The function uses pandas average-tie percentile ranking, scaled 0–100 and
rounded to one decimal place. A higher raw stat value receives a higher
percentile rank — ranks are not direction-adjusted for whether higher is
better for player evaluation. Identifier and metadata columns (`player_id`,
`name`, `first_name`, `last_name`, `name_ascii`, `slug`, `player_type`,
`opp_hand`) are excluded from ranking by default; pass a custom
`excluded_columns` argument to override.
