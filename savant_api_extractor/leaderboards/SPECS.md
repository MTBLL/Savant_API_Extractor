# Leaderboard endpoint specs

Live snapshot reference for every ETL-tier leaderboard, pulled fresh on **2026-05-13** for `year=2026`. Use this doc to verify schemas haven't drifted, debug mapping mismatches, and confirm what each endpoint actually returns in the wild.

Each section captures:
- The exact URL hit
- Live row count and column count
- Raw column list (the order Savant returns them in)
- Header mapping (raw → normalized) — driven by the config module
- Identity columns (the natural key for joins downstream)
- A raw Ohtani sample row (he's the cross-leaderboard anchor — present in all 8)

If Savant changes a column name or adds/removes columns, the live response will diverge from the raw-column list captured here. The handler will silently drop unmapped columns (intentional) so the practical failure mode is "downstream tables suddenly missing data," not a hard error. Re-run the snapshot when investigating.

> ⚠️ **Snapshot date matters.** Row counts and stat values are mid-season 2026 figures. Treat the schema (column names + types) as the contract; treat the values as illustrative.

---

## 1. `statcast_batter` — contact-quality leaderboard (hitting)

**URL:** `https://baseballsavant.mlb.com/leaderboard/statcast?type=batter&year=2026&csv=true`
**Today (2026-05-13):** 269 rows × 18 columns
**Identity:** `(player_id,)`

### Raw columns
```
last_name, first_name | player_id | attempts | avg_hit_angle | anglesweetspotpercent
max_hit_speed | avg_hit_speed | ev50 | fbld | gb | max_distance | avg_distance
avg_hr_distance | ev95plus | ev95percent | barrels | brl_percent | brl_pa
```

### Header mappings
| raw | renamed |
|---|---|
| `last_name, first_name` | `name` |
| `player_id` | `player_id` |
| `attempts` | `bbe` |
| `avg_hit_angle` | `avg_launch_angle` |
| `anglesweetspotpercent` | `sweetspot_pct` |
| `max_hit_speed` | `max_ev` |
| `avg_hit_speed` | `avg_ev` |
| `ev50` | `ev50` |
| `fbld` | `fbld_ev` |
| `gb` | `gb_ev` |
| `max_distance` | `max_distance` |
| `avg_distance` | `avg_distance` |
| `avg_hr_distance` | `avg_hr_distance` |
| `ev95plus` | `ev95_plus` |
| `ev95percent` | `ev95_pct` |
| `barrels` | `barrels` |
| `brl_percent` | `barrels_per_bbe_pct` |
| `brl_pa` | `barrels_per_pa_pct` |

### Ohtani sample (raw)
```json
{
  "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "attempts": 108, "avg_hit_angle": 11.0,
  "anglesweetspotpercent": 35.2, "max_hit_speed": 114.6, "avg_hit_speed": 92.9,
  "ev50": 102.3, "fbld": 96.1, "gb": 89.6,
  "max_distance": 438, "avg_distance": 175, "avg_hr_distance": 400.0,
  "ev95plus": 50, "ev95percent": 46.3,
  "barrels": 18, "brl_percent": 16.7, "brl_pa": 9.7
}
```

---

## 2. `statcast_pitcher` — contact-quality leaderboard (allowed)

**URL:** `https://baseballsavant.mlb.com/leaderboard/statcast?type=pitcher&year=2026&csv=true`
**Today (2026-05-13):** 367 rows × 18 columns
**Identity:** `(player_id,)`
**Schema:** identical to `statcast_batter` — same 18 raw columns, same mapping.

### Ohtani sample (raw)
```json
{
  "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "attempts": 91, "avg_hit_angle": 14.5,
  "anglesweetspotpercent": 19.8, "max_hit_speed": 111.2, "avg_hit_speed": 87.6,
  "ev50": 75.8, "fbld": 91.2, "gb": 88.5,
  "max_distance": 395, "avg_distance": 132, "avg_hr_distance": 366.0,
  "ev95plus": 35, "ev95percent": 38.5,
  "barrels": 3, "brl_percent": 3.3, "brl_pa": 2.1
}
```

---

## 3. `expected_statistics_batter` — Statcast x-stats (hitting)

**URL:** `https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=batter&year=2026&csv=true`
**Today (2026-05-13):** 269 rows × 14 columns
**Identity:** `(player_id, year)`

### Raw columns
```
last_name, first_name | player_id | year | pa | bip
ba | est_ba | est_ba_minus_ba_diff
slg | est_slg | est_slg_minus_slg_diff
woba | est_woba | est_woba_minus_woba_diff
```

### Header mappings
| raw | renamed |
|---|---|
| `last_name, first_name` | `name` |
| `player_id` | `player_id` |
| `year` | `year` |
| `pa` | `PA` |
| `bip` | `BIP` |
| `ba` | `AVG` |
| `est_ba` | `xAVG` |
| `est_ba_minus_ba_diff` | `xAVGdiff` |
| `slg` | `SLG` |
| `est_slg` | `xSLG` |
| `est_slg_minus_slg_diff` | `xSLGdiff` |
| `woba` | `wOBA` |
| `est_woba` | `xwOBA` |
| `est_woba_minus_woba_diff` | `wOBAdiff` |

### Ohtani sample (raw)
```json
{
  "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "year": 2026, "pa": 185, "bip": 108,
  "ba": 0.24, "est_ba": 0.256, "est_ba_minus_ba_diff": -0.016,
  "slg": 0.427, "est_slg": 0.49, "est_slg_minus_slg_diff": -0.063,
  "woba": 0.348, "est_woba": 0.38, "est_woba_minus_woba_diff": -0.032
}
```

---

## 4. `expected_statistics_pitcher` — Statcast x-stats (allowed) + xERA

**URL:** `https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=pitcher&year=2026&csv=true`
**Today (2026-05-13):** 367 rows × 17 columns
**Identity:** `(player_id, year)`

### Raw columns
```
(all 14 batter columns) + era | xera | era_minus_xera_diff
```

### Additional header mappings (beyond the batter set)
| raw | renamed |
|---|---|
| `era` | `ERA` |
| `xera` | `xERA` |
| `era_minus_xera_diff` | `xERAdiff` |

### Ohtani sample (raw)
```json
{
  "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "year": 2026, "pa": 145, "bip": 91,
  "ba": 0.16, "est_ba": 0.182, "est_ba_minus_ba_diff": -0.022,
  "slg": 0.26, "est_slg": 0.265, "est_slg_minus_slg_diff": -0.005,
  "woba": 0.226, "est_woba": 0.236, "est_woba_minus_woba_diff": -0.010,
  "era": 0.97, "xera": 2.17, "era_minus_xera_diff": -1.197
}
```

---

## 5. `home_runs_batter` — HR / xHR / park-adjusted variants (hit)

**URL:** `https://baseballsavant.mlb.com/leaderboard/home-runs?year=2026&csv=true`
**Today (2026-05-13):** 399 rows × 13 columns
**Identity:** `(player_id, year, hr_type)`

### Raw columns
```
player | player_id | team_abbrev | year | type
avg_hr_trot | doubters | mostly_gone | no_doubters | no_doubter_per
hr_total | xhr | xhr_diff
```

### Header mappings
| raw | renamed |
|---|---|
| `player` | `name` |
| `player_id` | `player_id` |
| `team_abbrev` | `team` |
| `year` | `year` |
| `type` | `hr_type` |
| `avg_hr_trot` | `avg_hr_trot` |
| `doubters` | `doubters` |
| `mostly_gone` | `mostly_gone` |
| `no_doubters` | `no_doubters` |
| `no_doubter_per` | `no_doubter_pct` |
| `hr_total` | `HR` |
| `xhr` | `xHR` |
| `xhr_diff` | `xHRdiff` |

> The `type` column distinguishes HR variants (e.g., `adj_xhr` for park-adjusted xHR rows). Identity key includes this column so downstream tables can store multiple variants per (player, year).

### Ohtani sample (raw)
```json
{
  "player": "Ohtani, Shohei",
  "player_id": 660271, "team_abbrev": "LAD", "year": 2026,
  "type": "adj_xhr", "avg_hr_trot": 24.19,
  "doubters": 4, "mostly_gone": 5, "no_doubters": 2, "no_doubter_per": 28.6,
  "hr_total": 7, "xhr": 5.5, "xhr_diff": 1.5
}
```

---

## 6. `home_runs_pitcher` — HR / xHR / park-adjusted (allowed)

**URL:** `https://baseballsavant.mlb.com/leaderboard/home-runs?player_type=Pitcher&year=2026&csv=true`
**Today (2026-05-13):** 504 rows × 13 columns
**Identity:** `(player_id, year, hr_type)`
**Schema:** identical to `home_runs_batter`.

### Ohtani sample (raw)
```json
{
  "player": "Ohtani, Shohei",
  "player_id": 660271, "team_abbrev": "LAD", "year": 2026,
  "type": "adj_xhr", "avg_hr_trot": 23.91,
  "doubters": 0, "mostly_gone": 2, "no_doubters": 1, "no_doubter_per": 50.0,
  "hr_total": 2, "xhr": 1.8, "xhr_diff": 0.2
}
```

---

## 7. `pitch_arsenal_stats_batter` — per-pitch outcomes (long-format)

**URL:** `https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats?type=batter&year=2026&csv=true`
**Today (2026-05-13):** 996 rows × 20 columns
**Identity:** `(player_id, pitch_type)` ← **long-format** on `pitch_type`
**Cardinality:** ~5 rows per batter (one per pitch type they've faced enough of)

### Raw columns
```
last_name, first_name | player_id | team_name_alt | pitch_type | pitch_name
run_value_per_100 | run_value | pitches | pitch_usage | pa
ba | slg | woba
whiff_percent | k_percent | put_away
est_ba | est_slg | est_woba | hard_hit_percent
```

### Header mappings
| raw | renamed |
|---|---|
| `last_name, first_name` | `name` |
| `player_id` | `player_id` |
| `team_name_alt` | `team` |
| `pitch_type` | `pitch_type` |
| `pitch_name` | `pitch_name` |
| `run_value_per_100` | `run_value_per_100` |
| `run_value` | `run_value` |
| `pitches` | `pitches` |
| `pitch_usage` | `pitch_usage_pct` |
| `pa` | `PA` |
| `ba` | `AVG` |
| `slg` | `SLG` |
| `woba` | `wOBA` |
| `whiff_percent` | `whiff_pct` |
| `k_percent` | `K%` |
| `put_away` | `put_away_pct` |
| `est_ba` | `xAVG` |
| `est_slg` | `xSLG` |
| `est_woba` | `xwOBA` |
| `hard_hit_percent` | `hardhit_pct` |

### Ohtani sample (raw — one of 5 rows; pitch_type=FF shown)
```json
{
  "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "team_name_alt": "LAD",
  "pitch_type": "FF", "pitch_name": "4-Seam Fastball",
  "run_value_per_100": -1.8, "run_value": -4,
  "pitches": 231, "pitch_usage": 32.4, "pa": 56,
  "ba": 0.174, "slg": 0.261, "woba": 0.275,
  "whiff_percent": 23.6, "k_percent": 28.6, "put_away": 27.1,
  "est_ba": 0.231, "est_slg": 0.411, "est_woba": 0.36,
  "hard_hit_percent": 46.9
}
```

---

## 8. `sprint_speed` — baserunning speed predictor for SB

**URL:** `https://baseballsavant.mlb.com/leaderboard/sprint_speed?year=2026&csv=true`
**Today (2026-05-13):** 401 rows × 10 columns
**Identity:** `(player_id,)`

### Raw columns
```
last_name, first_name | player_id | team_id | team | position | age
competitive_runs | bolts | hp_to_1b | sprint_speed
```

### Header mappings
| raw | renamed |
|---|---|
| `last_name, first_name` | `name` |
| `player_id` | `player_id` |
| `team_id` | `team_id` |
| `team` | `team` |
| `position` | `position` |
| `age` | `age` |
| `competitive_runs` | `competitive_runs` |
| `bolts` | `bolts` |
| `hp_to_1b` | `hp_to_1b` |
| `sprint_speed` | `sprint_speed` |

### Ohtani sample (raw)
```json
{
  "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "team_id": 119, "team": "LAD",
  "position": "DH", "age": 31, "competitive_runs": 53,
  "bolts": null, "hp_to_1b": 4.22, "sprint_speed": 27.1
}
```

---

## Re-running this snapshot

```bash
uv run python -c "
import requests, io, pandas as pd
from concurrent.futures import ThreadPoolExecutor
from savant_api_extractor.leaderboards import ETL_TIER_CONFIGS

YEAR = '2026'
BASE = 'https://baseballsavant.mlb.com/leaderboard/'

def fetch(cfg):
    params = {**dict(cfg.default_params), 'year': YEAR, 'csv': 'true'}
    r = requests.get(BASE + cfg.url_path, params=params, timeout=30)
    df = pd.read_csv(io.StringIO(r.text), low_memory=False)
    return cfg.name, len(df), len(df.columns), df.columns.tolist()

with ThreadPoolExecutor(max_workers=4) as ex:
    for name, rows, cols, columns in ex.map(fetch, ETL_TIER_CONFIGS):
        print(f'{name}: {rows} rows, {cols} cols')
        print(f'  cols: {columns}')
"
```
