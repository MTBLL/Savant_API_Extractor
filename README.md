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

## Using as a library

This package is also designed to be imported from other apps (e.g., the downstream MTBL analytics app). The top-level `savant_api_extractor/__init__.py` is intentionally empty — **nothing loads eagerly**. Each submodule is independently importable, and the cost of importing a given path is bounded by what that path actually needs.

### Install

This repo ships as a `uv` / `pip`-installable Python package via its `pyproject.toml`. From a consumer project:

```bash
# editable install during dev
uv add --editable /path/to/Savant_API_Extractor

# or from git
uv add "savant-api-extractor @ git+https://github.com/MTBLL/Savant_API_Extractor.git"
```

### Import map — what each entry point pulls in

The three main consumer-facing entry points have very different import footprints. Pick the one that matches your use case and avoid pulling in dependencies you don't need.

| Import path | What it gives you | Loads pandas/numpy? |
|---|---|---|
| `from savant_api_extractor.mlb_statsapi import fetch_probable_pitchers` | Daily probable pitchers via MLB StatsAPI | **No** — only `requests` + stdlib |
| `from savant_api_extractor.handlers import LeaderboardHandler` <br>`from savant_api_extractor.leaderboards import {config}` | Generic on-demand leaderboard CSV puller (ETL or RT tier) | **Yes** — returns DataFrames |
| `from savant_api_extractor.runner.savant_runner import SavantRunner` | Full bulk-extraction orchestrator (splits + ETL leaderboards) | **Yes** — full stack |

**For an analytics app pulling probable pitchers + ad-hoc matchup drill-downs**, the lightweight path is:

```python
# Probable pitchers — no pandas dependency
from savant_api_extractor.mlb_statsapi import fetch_probable_pitchers

# RT-tier leaderboard drill-down — pandas DataFrame
from savant_api_extractor.handlers import LeaderboardHandler
from savant_api_extractor.leaderboards import pitch_arsenals, pitch_movement

slate    = fetch_probable_pitchers("2026-05-13")           # list[dict]
handler  = LeaderboardHandler()
arsenal  = handler.extract(pitch_arsenals.CONFIG, year="2026")   # DataFrame
movement = handler.extract(pitch_movement.CONFIG, year="2026")   # DataFrame
```

The `SavantRunner` and the bulk-runner machinery do **not** load unless you explicitly import them. Same for the `BatterHandler` / `PitcherHandler` (which target the splits endpoint and are only used by the runner). An analytics app that just needs probable pitchers + on-demand leaderboards never touches those code paths.

### Sub-package overview

| Sub-package | Purpose | Loads when imported |
|---|---|---|
| `savant_api_extractor.mlb_statsapi` | MLB StatsAPI wrappers (probable pitchers today; player metadata etc. future) | `requests`, stdlib |
| `savant_api_extractor.handlers` | HTTP+CSV handler classes (BatterHandler, PitcherHandler, LeaderboardHandler) | pandas, requests |
| `savant_api_extractor.leaderboards` | LeaderboardConfig dataclasses for every Savant leaderboard (ETL and RT tiers) | lightweight (just dataclasses) |
| `savant_api_extractor.controller` | SavantController — builds query params for the splits endpoint | imports handlers ⇒ pandas |
| `savant_api_extractor.runner` | SavantRunner — bulk-extraction orchestrator | full stack |
| `savant_api_extractor.utils` | Logger, mappings, thresholds, name parser. Pandas-dependent helpers (e.g. `rounding`) live here too but are NOT re-exported by the package — import via the full path if needed | stdlib only via the re-exports |

## Output Files

A full `all` extraction writes **thirteen JSON files** to the output directory:

**Two handedness-split files** (from the `statcast_search` endpoint family):

- `savant_batters_YYYY_MM_DD_HHMM.json` — batter rows, up to 3 per player (one per `opp_hand`)
- `savant_pitchers_YYYY_MM_DD_HHMM.json` — pitcher rows, same shape

**Ten leaderboard files** (from the `/leaderboard/*?csv=true` endpoint family):

- `savant_statcast_batter_YYYY_MM_DD_HHMM.json` — contact quality (hit)
- `savant_statcast_pitcher_YYYY_MM_DD_HHMM.json` — contact quality (allowed)
- `savant_expected_statistics_pitcher_YYYY_MM_DD_HHMM.json` — x-stats (allowed) + xERA *(the batter variant is intentionally not pulled — its columns are already in the batter splits file)*
- `savant_home_runs_batter_YYYY_MM_DD_HHMM.json` — HR / xHR / park-adjusted (hit)
- `savant_home_runs_pitcher_YYYY_MM_DD_HHMM.json` — HR / xHR / park-adjusted (allowed)
- `savant_pitch_arsenal_stats_batter_YYYY_MM_DD_HHMM.json` — batter per-pitch outcomes (long on `pitch_type`)
- `savant_pitch_arsenal_stats_pitcher_YYYY_MM_DD_HHMM.json` — pitcher per-pitch outcomes (long on `pitch_type`)
- `savant_sprint_speed_YYYY_MM_DD_HHMM.json` — baserunning speed + bolts
- `savant_swing_take_batter_YYYY_MM_DD_HHMM.json` — Statcast Run Value Leaderboard (batting): `runs_all` + zone decomposition
- `savant_swing_take_pitcher_YYYY_MM_DD_HHMM.json` — Statcast Run Value Leaderboard (pitching): same schema, runs prevented

**One state-inlined SSR file** (`/leaderboard/rolling` — HTML, not `?csv=true`):

- `savant_rolling_YYYY_MM_DD_HHMM.json` — rolling-window form: most-recent-N-PA vs prior-N-PA deltas (50/100/250 windows), long on `(cat, cat_bin)`. The page embeds the dataset as a `var rolling = {...}` JS variable; the handler regex-extracts and `json.loads`-es it. See SPECS.md Part III.

Each file is a JSON array of row objects, joinable on `player_id`. See [Leaderboard extracts](#leaderboard-extracts) below for the data contract and `savant_api_extractor/leaderboards/SPECS.md` for live per-endpoint snapshots.

To skip the leaderboard pulls (splits only), construct the runner with `include_leaderboards=False`.

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

The ten `savant_{slug}_*.json` leaderboard files are independent extracts of Savant's `/leaderboard/{slug}?csv=true` endpoints — different schemas, different identity keys, joinable on `player_id` downstream. The `savant_rolling_*.json` file is also leaderboard-derived, but the rolling page is state-inlined SSR rather than a `?csv=true` endpoint (see its row below and SPECS.md Part III).

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
| `swing_take_batter` | `(player_id, year)` | OBP, overall batting value — run value + zone decomposition |
| `swing_take_pitcher` | `(player_id, year)` | ERA, WHIP — run value prevented (same schema as batter) |
| `rolling` | `(player_id, cat, cat_bin)` | recent form — rolling-window deltas (state-inlined SSR; long-format) |

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

#### `BirthdayIndexHandler` — RT-tier, state-inlined SSR

Beyond the config-driven RT leaderboards above, `BirthdayIndexHandler` covers the Savant `/birthday-index` page (Sarah Langs' Birthday Index — a player's wOBA on their birthday vs. other days; a streaming-pitcher / platoon start-sit signal). It's RT-tier like the configs, but a dedicated handler rather than a `LeaderboardConfig`: the page is state-inlined SSR (no `?csv=true`), extracted the same way as the bulk `RollingHandler`. `extract(player_type="batter" | "pitcher")` returns **active players only** — the raw page is ~90% retired/historical. See SPECS.md Part III (SSR-2).

For full per-endpoint column lists, header mappings, and live snapshot samples, see [`savant_api_extractor/leaderboards/SPECS.md`](savant_api_extractor/leaderboards/SPECS.md) (Part II: RT-tier endpoints).

## MLB StatsAPI integration

Alongside the Savant client, this package ships a small wrapper around the official **MLB StatsAPI** (`statsapi.mlb.com`) — public, no auth required. It lives here because the same analytics pipeline that consumes Savant data also needs daily probable-pitcher info to drive matchup views, and there's no reason to scrape the Savant `/probable-pitchers` HTML page when the canonical source returns clean JSON.

### `fetch_probable_pitchers(date)` — daily slate

```python
from datetime import date
from savant_api_extractor.mlb_statsapi import fetch_probable_pitchers

slate = fetch_probable_pitchers(date.today())
# Returns: list[dict], one per scheduled game
```

Each row carries:

| Field | Type | Example |
|---|---|---|
| `gamePk` | int | `776315` |
| `gameDate` | str (ISO 8601 UTC) | `"2025-09-15T22:45:00Z"` |
| `gameState` | str | `"Preview"` / `"Live"` / `"Final"` |
| `away_team_code` | str | `"atl"` (3-letter MLB internal code) |
| `away_team_name` | str | `"Atlanta Braves"` |
| `away_probable_id` | int \| None | `675911` (None if TBD) |
| `away_probable_name` | str \| None | `"Spencer Strider"` (None if TBD) |
| `home_team_code` | str | `"was"` |
| `home_team_name` | str | `"Washington Nationals"` |
| `home_probable_id` | int \| None | `680730` |
| `home_probable_name` | str \| None | `"Mitchell Parker"` |

Notes:
- **Team codes are MLB's 3-letter lowercase internal codes** (`nya` for Yankees, `lan` for Dodgers), not the more familiar `NYY`/`LAD` codes used in Statcast. If your downstream needs the Statcast form, map at the consumer.
- **Probable pitcher is `None` when not announced.** Don't expect both teams' pitchers to be set for every game — schedules often announce one side first.
- **No caching here.** Like the RT-tier leaderboard configs, this is the network layer only — call from your analytics app and cache per-request as appropriate.

### Endpoint hit

```
GET https://statsapi.mlb.com/api/v1/schedule
    ?sportId=1
    &date=YYYY-MM-DD
    &hydrate=probablePitcher,team,lineups
```

The MLB StatsAPI is undocumented officially but publicly accessible; community references at [toddrob99/MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI).

### Barrel and Hard-Hit Metrics

Both batter and pitcher exports include these contact-quality fields:

- `hardhit_pct`
- `barrels_per_bbe_pct`
- `barrels_per_pa_pct`
- `barrels_total`

Percentage fields are exported on Baseball Savant's percentage scale, not as
fractions. For example, `35.0` means 35%.

### Percentile Ranks (computed downstream, not at extract time)

The extractor emits **raw stat values only**. Percentile ranks are not
applied at extract time — they're only meaningful relative to a reference
cohort, and that choice is a transform-layer decision.

Computing ranks at extract time would lock all downstream consumers to one
cohort definition. Cohort mismatch inverts the rank signal at the tails (a
90th-percentile fantasy hitter looks like a 75th-percentile MLB hitter, and
vice versa). The extractor's job is to produce raw values; the T layer
builds its own reference cohorts and ranks against them.

The canonical T-layer implementation lives at
`_transform/MTBL_Valuations/mtbl_valuations/io/savant_ranks.py`.

## Testing

Two layers, run separately:

- **Unit tests** — `uv run pytest tests/` (or just `uv run pytest`). Fast, hermetic, no network: handlers and configs are exercised against captured fixtures under `tests/fixtures/`. This is what the pre-push git hook and the PR/push CI run, gated at 100% coverage.
- **Integration tests** — `uv run pytest -m integration`. These hit the **live** Savant / MLB StatsAPI endpoints and assert the response *shape* (column/key sets, non-empty, types) still matches what the code expects. They are **excluded from the default run** so a Savant outage or template change can't block an unrelated push or PR; a weekly scheduled job (`.github/workflows/integration.yml`) runs them, and you can trigger it on demand via `workflow_dispatch`.

The two layers are complementary: fixture unit tests prove the *parse logic* is correct; integration tests catch Savant *drifting* the source out from under a frozen fixture.
