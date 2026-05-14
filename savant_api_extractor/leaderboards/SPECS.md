# Leaderboard endpoint specs

Live snapshot reference for every ETL-tier leaderboard, pulled fresh on **2026-05-13** for `year=2026`. Use this doc to verify schemas haven't drifted, debug mapping mismatches, and confirm what each endpoint actually returns in the wild.

Each section captures:
- The exact URL hit
- Live row count and column count
- Raw column list (the order Savant returns them in)
- Header mapping (raw → normalized) — driven by the config module
- Identity columns (the natural key for joins downstream)
- A raw Ohtani sample row (he's the cross-leaderboard anchor — present in all 10)

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

## 3. `expected_statistics_pitcher` — Statcast x-stats (allowed) + xERA

**URL:** `https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=pitcher&year=2026&csv=true`
**Today (2026-05-13):** 367 rows × 17 columns
**Identity:** `(player_id, year)`

> The batter variant of this endpoint is **intentionally not ETL'd** — every column it provides (PA, AVG, xAVG, xAVGdiff, SLG, xSLG, xSLGdiff, wOBA, xwOBA, wOBAdiff, BIP) is also returned by the `statcast_search` endpoint that feeds the `savant_batters_*.json` splits file. The pitcher variant is kept here because it's the **only source of `xERA` / `xERAdiff`** in the entire Savant catalog.

### Raw columns
```
last_name, first_name | player_id | year | pa | bip
ba | est_ba | est_ba_minus_ba_diff
slg | est_slg | est_slg_minus_slg_diff
woba | est_woba | est_woba_minus_woba_diff
era | xera | era_minus_xera_diff
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

## 4. `home_runs_batter` — HR / xHR / park-adjusted variants (hit)

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

## 5. `home_runs_pitcher` — HR / xHR / park-adjusted (allowed)

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

## 6. `pitch_arsenal_stats_batter` — per-pitch outcomes (long-format, hitting)

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

## 7. `pitch_arsenal_stats_pitcher` — per-pitch outcomes (long-format, pitching)

**URL:** `https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats?type=pitcher&year=2026&csv=true`
**Today (2026-05-13):** 613 rows × 20 columns
**Identity:** `(player_id, pitch_type)` ← **long-format** on `pitch_type`
**Cardinality:** ~2-5 rows per pitcher (one per pitch type in their arsenal that meets Savant's threshold)
**Schema:** identical to `pitch_arsenal_stats_batter` — same 20 raw columns, same mapping. Only the perspective flips (these are *thrown* pitches with the outcomes the pitcher allowed; the batter variant is *faced* pitches with the outcomes the batter produced).

> This is the pitcher-archetype side of the matchup join. Combine with `pitch_arsenal_stats_batter` on `pitch_type` to project at-bat outcomes for a specific batter against a specific pitcher's arsenal.

### Ohtani sample (raw — Ohtani has 2 rows as a pitcher; pitch_type=FF shown)
```json
{
  "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "team_name_alt": "LAD",
  "pitch_type": "FF", "pitch_name": "4-Seam Fastball",
  "run_value_per_100": -0.8, "run_value": -2,
  "pitches": 250, "pitch_usage": 44.5, "pa": 68,
  "ba": 0.207, "slg": 0.276, "woba": 0.270,
  "whiff_percent": 27.1, "k_percent": 27.9, "put_away": 26.0,
  "est_ba": 0.222, "est_slg": 0.341, "est_woba": 0.238,
  "hard_hit_percent": 32.6
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

## 9. `swing_take_batter` — Statcast Run Value Leaderboard (batting)

**URL:** `https://baseballsavant.mlb.com/leaderboard/swing-take?year=2026&team=&leverage=Neutral&group=Batter&type=All&sub_type=null&min=q&csv=true`
**Today (2026-05-14):** 300 rows × 11 columns
**Identity:** `(player_id, year)`

> ⚠️ **Full canonical param set required.** A bare `?type=batter&csv=true` returns a header-only response — Savant's SSR template needs all of `team`, `leverage`, `group`, `type`, `sub_type`, `min` present or it serves an empty dataset. Context-Neutral only (`leverage=Neutral`); the page's alternate UI decompositions (swing/take split, pitch-type cross-tab) are out of scope.

### Raw columns
```
year | last_name, first_name | player_id | team_id | pa | pitches
runs_all | runs_heart | runs_shadow | runs_chase | runs_waste
```

### Header mappings
| raw | renamed |
|---|---|
| `year` | `year` |
| `last_name, first_name` | `name` |
| `player_id` | `player_id` |
| `team_id` | `team_id` |
| `pa` | `PA` |
| `pitches` | `pitches` |
| `runs_all` | `runs_all` |
| `runs_heart` | `runs_heart` |
| `runs_shadow` | `runs_shadow` |
| `runs_chase` | `runs_chase` |
| `runs_waste` | `runs_waste` |

`runs_all` is the season-total run value; `runs_heart`/`runs_shadow`/`runs_chase`/`runs_waste` decompose it by Savant attack zone. Positive = runs created.

### Ohtani sample (raw)
```json
{
  "year": 2026, "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "team_id": 119, "pa": 179, "pitches": 714,
  "runs_all": 3.73, "runs_heart": -8.35, "runs_shadow": 0.69,
  "runs_chase": 5.94, "runs_waste": 5.44
}
```

---

## 10. `swing_take_pitcher` — Statcast Run Value Leaderboard (pitching)

**URL:** `https://baseballsavant.mlb.com/leaderboard/swing-take?year=2026&team=&leverage=Neutral&group=Pitcher&type=All&sub_type=null&min=q&csv=true`
**Today (2026-05-14):** 300 rows × 11 columns
**Identity:** `(player_id, year)`
**Schema:** identical to `swing_take_batter` — same 11 raw columns, same mapping. Only the `group` param flips (`Pitcher`). Sign convention flips with it: positive `runs_*` = runs prevented (good for the pitcher).

### Ohtani sample (raw)
```json
{
  "year": 2026, "last_name, first_name": "Ohtani, Shohei",
  "player_id": 660271, "team_id": 119, "pa": 171, "pitches": 667,
  "runs_all": 14.27, "runs_heart": 13.95, "runs_shadow": 4.05,
  "runs_chase": -1.02, "runs_waste": -2.72
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

---

# Part II: RT-tier endpoints

The endpoints below are **not pulled by the bulk runner** (`SavantRunner.run`). They live in `RT_TIER_CONFIGS` and are imported on-demand by the analytics app — typically for matchup drill-downs (probable-pitcher arsenal, batter swing profile, batted-ball direction). Same `LeaderboardHandler` consumes them; same Ohtani-anchored fixtures cover them in tests.

---

## RT-1. `pitch_arsenals` — per-pitch avg velocity per pitcher (wide-format)

**URL:** `https://baseballsavant.mlb.com/leaderboard/pitch-arsenals?year=2026&csv=true`
**Today (2026-05-13):** 365 rows × 12 columns
**Identity:** `(player_id,)`
**Shape:** wide on pitch type — one column per pitch-type code (ff/si/fc/sl/ch/cu/fs/kn/st/sv). NaN cells for pitches the pitcher doesn't throw.

### Header mappings
| raw | renamed |
|---|---|
| `last_name, first_name` | `name` |
| `pitcher` | `player_id` |
| `{type}_avg_speed` | `{type}_avg_speed` (preserved) |

### Ohtani sample (raw)
```json
{
  "last_name, first_name": "Ohtani, Shohei", "pitcher": 660271,
  "ff_avg_speed": 98.0, "si_avg_speed": 95.7, "fc_avg_speed": 91.8,
  "sl_avg_speed": 87.4, "ch_avg_speed": null, "cu_avg_speed": 74.5
}
```

---

## RT-2. `pitch_movement` — per-pitch break vs league (long-format)

**URL:** `https://baseballsavant.mlb.com/leaderboard/pitch-movement?year=2026&csv=true`
**Today (2026-05-13):** 383 rows × 24 columns
**Identity:** `(player_id, pitch_type, year)`
**Shape:** long-format — one row per (pitcher, pitch_type, year). Strongest single proxy for "stuff" quality; the `diff_z`/`diff_x` columns normalize against league average for that pitch type.

### Header mappings
| raw | renamed |
|---|---|
| `last_name, first_name` | `name` |
| `pitcher_id` | `player_id` |
| `pitch_type_name` | `pitch_name` |
| `pitcher_break_z` | `break_z` |
| `pitcher_break_z_induced` | `break_z_induced` |
| `pitcher_break_x` | `break_x` |
| `percent_rank_diff_z` | `pct_rank_diff_z` |
| `percent_rank_diff_x` | `pct_rank_diff_x` |
| `team_name_abbrev` | `team` |
| `pitch_type`, `pitch_hand`, `avg_speed`, `diff_z`, `rise`, `diff_x`, `tail`, `league_break_z`, `league_break_x`, `pitches_thrown`, `total_pitches`, `pitches_per_game`, `pitch_per`, `team_name`, `year` | (preserved) |

### Ohtani sample (raw — one of multiple rows; pitch_type=FF shown)
```json
{
  "year": 2026, "last_name, first_name": "Ohtani, Shohei", "pitcher_id": 660271,
  "team_name": "Dodgers", "team_name_abbrev": "LAD",
  "pitch_hand": "R", "avg_speed": 98.0, "pitch_type": "FF",
  "pitches_thrown": 250
}
```

---

## RT-3. `active_spin` — active-spin % per pitch type per pitcher (wide-format)

**URL:** `https://baseballsavant.mlb.com/leaderboard/active-spin?year=2026&csv=true`
**Today (2026-05-13):** 452 rows × 12 columns
**Identity:** `(player_id,)`
**Shape:** wide on pitch type. Active spin is the % of total spin that contributes to movement vs. gyroscopic spin. Higher % = more "ride" / "drop".

### Header mappings
| raw | renamed |
|---|---|
| `entity_name` | `name` |
| `entity_id` | `player_id` |
| `pitch_hand` | `pitch_hand` |
| `active_spin_fourseam` | `active_spin_ff` |
| `active_spin_sinker` | `active_spin_si` |
| `active_spin_cutter` | `active_spin_fc` |
| `active_spin_changeup` | `active_spin_ch` |
| `active_spin_splitter` | `active_spin_fs` |
| `active_spin_curve` | `active_spin_cu` |
| `active_spin_slider` | `active_spin_sl` |
| `active_spin_sweeper` | `active_spin_st` |
| `active_spin_slurve` | `active_spin_sv` |

Pitch-type codes match `pitch_arsenals` so the two are directly join-able on (player_id, pitch_type) after pivoting either to long.

### Ohtani sample (raw)
```json
{
  "entity_name": "Ohtani, Shohei", "entity_id": 660271, "pitch_hand": "R",
  "active_spin_fourseam": 74.6, "active_spin_sinker": 70.6,
  "active_spin_cutter": null, "active_spin_changeup": null,
  "active_spin_splitter": 69.7
}
```

---

## RT-4. `pitcher_arm_angles` — release point / arm slot

**URL:** `https://baseballsavant.mlb.com/leaderboard/pitcher-arm-angles?year=2026&csv=true`
**Today (2026-05-13):** 306 rows × 10 columns
**Identity:** `(player_id,)`

### Header mappings
| raw | renamed |
|---|---|
| `pitcher` | `player_id` |
| `pitcher_name` | `name` |
| `pitch_hand` | `pitch_hand` |
| `n_pitches` | `n_pitches` |
| `team_id` | `team_id` |
| `ball_angle` | `ball_angle` |
| `relative_release_ball_x` | `release_ball_x_rel` |
| `release_ball_z` | `release_ball_z` |
| `relative_shoulder_x` | `shoulder_x_rel` |
| `shoulder_z` | `shoulder_z` |

### Ohtani sample (raw)
```json
{
  "pitcher": 660271, "pitcher_name": "Ohtani, Shohei",
  "pitch_hand": "R", "n_pitches": 562, "team_id": 119,
  "ball_angle": 34.9, "relative_release_ball_x": -2.02, "release_ball_z": 5.73
}
```

---

## RT-5. `bat_tracking_swing_path` — batter swing diagnostics

**URL:** `https://baseballsavant.mlb.com/leaderboard/bat-tracking/swing-path-attack-angle?year=2026&csv=true`
**Today (2026-05-13):** 224 rows × 13 columns
**Identity:** `(player_id, stands)`
**Shape:** one row per (batter, batting side). Switch-hitters get two rows.

### Header mappings
| raw | renamed |
|---|---|
| `id` | `player_id` |
| `name` | `name` |
| `side` | `stands` |
| `avg_bat_speed`, `swing_tilt`, `attack_angle`, `attack_direction`, `ideal_attack_angle_rate`, `avg_intercept_y_vs_plate`, `avg_intercept_y_vs_batter`, `avg_batter_y_position`, `avg_batter_x_position`, `competitive_swings` | (preserved) |

### Ohtani sample (raw, side=L)
```json
{
  "id": 660271, "name": "Ohtani, Shohei", "side": "L",
  "avg_bat_speed": 74.69, "swing_tilt": 37.5, "attack_angle": 13.3,
  "attack_direction": -0.25, "ideal_attack_angle_rate": 0.534
}
```

---

## RT-6. `batted_ball_batter` — batted-ball type + pull-direction rates

**URL:** `https://baseballsavant.mlb.com/leaderboard/batted-ball?type=batter&year=2026&csv=true`
**Today (2026-05-13):** 270 rows × 17 columns
**Identity:** `(player_id,)`

Contains `pull_air_rate` — a strong HR predictor (pull + elevate is the homer formula).

### Header mappings
All raw columns are preserved: `id` → `player_id`, `name` → `name`, plus rate columns (`bbe`, `gb_rate`, `air_rate`, `fb_rate`, `ld_rate`, `pu_rate`, `pull_rate`, `straight_rate`, `oppo_rate`, `pull_gb_rate`, `straight_gb_rate`, `oppo_gb_rate`, `pull_air_rate`, `straight_air_rate`, `oppo_air_rate`).

### Ohtani sample (raw)
```json
{
  "id": 660271, "name": "Ohtani, Shohei", "bbe": 108,
  "gb_rate": 0.463, "air_rate": 0.537, "fb_rate": 0.352, "ld_rate": 0.167,
  "pull_air_rate": ...
}
```

---

# Part III: State-inlined SSR leaderboards

The endpoints below are **not** `?csv=true` CSV endpoints. Each page is
*state-inlined SSR* — Savant renders the HTML and embeds the entire dataset as
a JavaScript variable assignment inside a `<script>` tag; `?csv=true` returns
the same HTML. Each gets a dedicated handler that fetches the HTML,
regex-extracts the variable, and `json.loads`-es it. If Savant ever migrates
one to a real XHR/JSON endpoint (consistent with their newer leaderboards),
switch to that — it would be strictly simpler.

| Endpoint | Tier | Handler |
|---|---|---|
| SSR-1 `rolling` | ETL (bulk runner) | `handlers/rolling_handler.py` |
| SSR-2 `birthday-index` | RT (analytics-app on-demand) | `handlers/birthday_index_handler.py` |

---

## SSR-1. `rolling` — rolling-window form leaderboard

**URL:** `https://baseballsavant.mlb.com/leaderboard/rolling`
**Today (2026-05-14):** ~2,400 rows × 27 columns (post-mapping, incl. name-parser additions)
**Identity:** `(player_id, cat, cat_bin)` ← **long-format** on role × window size

The inlined `var rolling` object has 6 keys — `{Batter,Pitcher} × {50,100,250}`
(role × window size in PA) — each holding a row list. The handler flattens all
6 lists into one long-format DataFrame; every row already carries `cat` and
`cat_bin`, so no identity columns need to be derived from the dict key.

Each row compares a player's most-recent-N-PA window to the prior-N-PA window
of the same size, across six rate stats. Raw columns: `last_x_<stat>`,
`penultimate_x_<stat>`, `<stat>_delta` for `<stat>` in
`{ba, slg, woba, xba, xslg, xwoba}`.

### Header mappings
| raw | renamed |
|---|---|
| `player_id` | `player_id` |
| `player_name` | `name` |
| `player_team_id` | `player_team_id` |
| `cat` | `cat` |
| `cat_bin` | `cat_bin` |
| `last_x_<stat>` | `last_<STAT>` |
| `penultimate_x_<stat>` | `prev_<STAT>` |
| `<stat>_delta` | `<STAT>_delta` |

`<STAT>` is the conventional sabermetric casing: `ba`→`BA`, `slg`→`SLG`,
`woba`→`wOBA`, `xba`→`xBA`, `xslg`→`xSLG`, `xwoba`→`xwOBA`. Savant's own `slug`
and `type_cat_bin` columns are unmapped and dropped — `type_cat_bin` is
redundant with `cat` + `cat_bin`, and Savant's `slug` format conflicts with
the name-parser `slug`.

### Sample row (raw, Batter50)
```json
{
  "player_name": "Vientos, Mark", "player_id": 668901,
  "player_team_id": 121, "cat": "Batter", "cat_bin": "50",
  "last_x_xwoba": 0.487, "penultimate_x_xwoba": 0.219, "xwoba_delta": 0.268,
  "last_x_woba": 0.35, "penultimate_x_woba": 0.178, "woba_delta": 0.172,
  "last_x_ba": 0.239, "penultimate_x_ba": 0.149, "ba_delta": 0.09
}
```

### Fixture
`tests/fixtures/leaderboards/rolling.html` — a trimmed (~12 KB) capture of the
1.6 MB live page: each of the 6 categories trimmed to 3 rows, with the
`<script>` wrapper and the `var rolling = {...};` assignment preserved verbatim
so the extraction regex is exercised against representative markup.

---

## SSR-2. `birthday-index` — Sarah Langs' Birthday Index

**URL:** `https://baseballsavant.mlb.com/birthday-index?type={batter,pitcher}`
**Today (2026-05-14):** ~224 active batters / ~141 active pitchers × 33 columns (post-mapping + active filter, incl. name-parser additions)
**Identity:** `(player_id, player_type)`
**Tier:** RT — `BirthdayIndexHandler`, analytics-app on-demand. NOT pulled by the bulk runner.

The "Birthday Index" is a Savant-computed stat: a player's wOBA on their
birthday vs. all other dates, sample-weighted by birthday PAs. Fantasy use:
streaming-pitcher selection and bench/platoon start-sit — the `daysUntil`
column makes the "look a couple days out" workflow native.

The page embeds two `const` arrays in a `<script>` block: `birthdayData` (the
"Upcoming Birthdays" table — the one the handler extracts) and `todayData`.
**Note `const`, not `var`** — the `RollingHandler` regex would not match.
`?type=pitcher` flips the page to the pitcher table; the handler takes a
`player_type` arg.

### Active-player filter
The raw `birthdayData` array is ~90% retired/historical players (the page's
birthday data goes back to 1969): ~2,069 batter rows of which only ~224 are
active, ~1,274 pitcher rows of which ~141 are active. `extract` filters to
`is_player_active == 1` before mapping — the `is_player_active` /
`is_player_deceased` flags are consumed by the filter and not emitted.

### Header mappings
Mostly identity — the raw column names are already clean. Dropped by omission:
`player_name` (dup of `name`), `id` (dup of `player_id`), `is_player_active` /
`is_player_deceased` (filter inputs), the `*_hidden` sort-helpers, and
`dateString` (a display string). Kept: `player_id`, `name`, `player_type`,
`actual_birthday`, `birth_day_noyear`, `age`, `daysUntil`, `isBirthday`,
`birthday_index`, `birthday_games`, `birthday_pa`, the
`birthday_{BA,OPS,wOBA}` + `non_birthday_*` + `*_diff` split triples, and the
`birthday_hit_*` / `birthday_strikeout` / `birthday_walk` / `*_percent`
counting + rate stats.

### Sample row (raw)
```json
{
  "player_name": "Cole Young", "name": "Cole Young",
  "player_id": 702284, "id": 702284, "player_type": "Batter",
  "is_player_active": 1, "is_player_deceased": 0,
  "actual_birthday": "2003-07-29T00:00:00.000Z", "birth_day_noyear": "7-29",
  "birthday_index": -1, "birthday_games": 1, "birthday_pa": 4,
  "birthday_BA": 0, "non_birthday_BA": 0.23, "birthday_BA_diff": -0.23
}
```

### Fixture
`tests/fixtures/leaderboards/birthday_index.html` — a trimmed (~5 KB) capture
of the ~1.95 MB live page: the `birthdayData` array cut to **3 active + 2
inactive rows** so the active-player filter is exercised, with the `<script>`
wrapper and the `const` declarations preserved verbatim so the extraction
regex runs as in the wild.
