"""Query parameter constants for Baseball Savant Statcast Search API.

This module documents all available query parameters for the Baseball Savant
Statcast Search CSV endpoint. Parameters are organized by category for easy reference.

Reference: https://baseballsavant.mlb.com/statcast_search
"""

from typing import Final

# ============================================================================
# Player Type
# ============================================================================

PLAYER_TYPE_BATTER: Final[str] = "batter"
PLAYER_TYPE_PITCHER: Final[str] = "pitcher"

# ============================================================================
# Pitch Filters (hfPT, hfPR, etc.)
# ============================================================================

# Pitch Type (hfPT)
# Values: Empty string or specific pitch type codes
HF_PITCH_TYPE: Final[str] = "hfPT"

# Pitch Result (hfPR)
# Values: Empty string or specific pitch result codes
HF_PITCH_RESULT: Final[str] = "hfPR"

# Zone (hfZ)
# Values: Empty string or zone numbers (1-13)
HF_ZONE: Final[str] = "hfZ"

# ============================================================================
# At Bat Filters
# ============================================================================

# At Bat Result (hfAB)
# Values: Empty string or specific at-bat result codes
HF_AT_BAT_RESULT: Final[str] = "hfAB"

# Batted Ball Location (hfBBL)
# Values: Empty string or location codes
HF_BATTED_BALL_LOCATION: Final[str] = "hfBBL"

# Pull Direction (hfPull)
# Values: Empty string or pull direction codes
HF_PULL: Final[str] = "hfPull"

# Count (hfC)
# Values: Empty string or count codes (e.g., "0-0", "3-2")
HF_COUNT: Final[str] = "hfC"

# ============================================================================
# Game Filters
# ============================================================================

# Game Type (hfGT)
# Values: Pipe-separated codes (e.g., "R|" for regular season)
# Common values: "R" (Regular Season), "PO" (Playoffs), "S" (Spring Training), etc.
HF_GAME_TYPE: Final[str] = "hfGT"
GAME_TYPE_SPRING_TRAINING: Final[str] = "S"
GAME_TYPE_REGULAR: Final[str] = "R"
GAME_TYPE_PLAYOFFS: Final[str] = "PO"

# Season (hfSea)
# Values: Pipe-separated years (e.g., "2025|")
HF_SEASON: Final[str] = "hfSea"

# Month (hfMo)
# Values: Empty string or month numbers (1-12)
HF_MONTH: Final[str] = "hfMo"

# Game Date Greater Than (game_date_gt)
# Values: Date in YYYY-MM-DD format
GAME_DATE_GT: Final[str] = "game_date_gt"

# Game Date Less Than (game_date_lt)
# Values: Date in YYYY-MM-DD format
GAME_DATE_LT: Final[str] = "game_date_lt"

# Stadium (hfStadium)
# Values: Empty string or stadium codes
HF_STADIUM: Final[str] = "hfStadium"

# Home/Road (home_road)
# Values: Empty string, "home", or "road"
HOME_ROAD: Final[str] = "home_road"
HOME_ROAD_HOME: Final[str] = "home"
HOME_ROAD_ROAD: Final[str] = "road"

# ============================================================================
# Player Filters
# ============================================================================

# Pitcher Throws (pitcher_throws)
# Values: Empty string, "L" (Left), or "R" (Right)
PITCHER_THROWS: Final[str] = "pitcher_throws"
PITCHER_THROWS_LEFT: Final[str] = "L"
PITCHER_THROWS_RIGHT: Final[str] = "R"

# Batter Stands (batter_stands)
# Values: Empty string, "L" (Left), or "R" (Right)
BATTER_STANDS: Final[str] = "batter_stands"
BATTER_STANDS_LEFT: Final[str] = "L"
BATTER_STANDS_RIGHT: Final[str] = "R"

# Position (position)
# Values: Empty string or position numbers (1-9)
POSITION: Final[str] = "position"

# Team (hfTeam)
# Values: Empty string or team codes
HF_TEAM: Final[str] = "hfTeam"

# Opponent (hfOpponent)
# Values: Empty string or opponent team codes
HF_OPPONENT: Final[str] = "hfOpponent"

# ============================================================================
# Situation Filters
# ============================================================================

# Situation (hfSit)
# Values: Empty string or situation codes
HF_SITUATION: Final[str] = "hfSit"

# Outs (hfOuts)
# Values: Empty string or number of outs (0, 1, 2)
HF_OUTS: Final[str] = "hfOuts"

# Inning (hfInn)
# Values: Empty string or inning numbers
HF_INNING: Final[str] = "hfInn"

# Runner On Base (hfRO)
# Values: Empty string or runner position codes
HF_RUNNER_ON: Final[str] = "hfRO"

# Infield Position (hfInfield)
# Values: Empty string or infield position codes
HF_INFIELD: Final[str] = "hfInfield"

# Outfield Position (hfOutfield)
# Values: Empty string or outfield position codes
HF_OUTFIELD: Final[str] = "hfOutfield"

# ============================================================================
# Advanced Filters
# ============================================================================

# New Zones (hfNewZones)
# Values: Empty string or zone codes
HF_NEW_ZONES: Final[str] = "hfNewZones"

# Special Attributes (hfSA)
# Values: Empty string or special attribute codes
HF_SPECIAL_ATTRIBUTES: Final[str] = "hfSA"

# Event Outs (hfEventOuts)
# Values: Empty string or event out codes
HF_EVENT_OUTS: Final[str] = "hfEventOuts"

# Event Runs (hfEventRuns)
# Values: Empty string or event run codes
HF_EVENT_RUNS: Final[str] = "hfEventRuns"

# BBT (hfBBT)
# Values: Empty string or BBT codes
HF_BBT: Final[str] = "hfBBT"

# Flags (hfFlag)
# Values: Pipe-separated flag codes with escaped dots
# Example: "is\\.bunt\\.not|is\\.competitive|"
# Common flags: "is.bunt.not", "is.competitive"
HF_FLAG: Final[str] = "hfFlag"
FLAG_NOT_BUNT: Final[str] = "is\\.bunt\\.not"
FLAG_COMPETITIVE: Final[str] = "is\\.competitive"

# ============================================================================
# Sorting & Grouping
# ============================================================================

# Sort Column (sort_col)
# Values: Column name to sort by (e.g., "xwoba", "ba", "slg")
SORT_COLUMN: Final[str] = "sort_col"
SORT_COL_XWOBA: Final[str] = "xwoba"
SORT_COL_BA: Final[str] = "ba"
SORT_COL_SLG: Final[str] = "slg"
SORT_COL_WOBA: Final[str] = "woba"

# Sort Order (sort_order)
# Values: "asc" (ascending) or "desc" (descending)
SORT_ORDER: Final[str] = "sort_order"
SORT_ORDER_ASC: Final[str] = "asc"
SORT_ORDER_DESC: Final[str] = "desc"

# Player Event Sort (player_event_sort)
# Values: Column name for player event sorting (e.g., "api_p_release_speed")
PLAYER_EVENT_SORT: Final[str] = "player_event_sort"
PLAYER_EVENT_SORT_RELEASE_SPEED: Final[str] = "api_p_release_speed"

# Group By (group_by)
# Values: Column name to group by (e.g., "name", "team")
GROUP_BY: Final[str] = "group_by"
GROUP_BY_NAME: Final[str] = "name"
GROUP_BY_TEAM: Final[str] = "team"

# ============================================================================
# Minimum Thresholds
# ============================================================================

# Minimum Pitches (min_pitches)
# Values: Integer (default: 0)
MIN_PITCHES: Final[str] = "min_pitches"

# Minimum Results (min_results)
# Values: Integer (default: 0)
MIN_RESULTS: Final[str] = "min_results"

# Minimum Plate Appearances (min_pas)
# Values: Integer (default: 0, example: 30)
MIN_PLATE_APPEARANCES: Final[str] = "min_pas"

# ============================================================================
# Statistics to Include (chk_stats_*)
# ============================================================================

# Check Stats - K% (chk_stats_k_percent)
# Values: "on" to include, empty string to exclude
CHK_STATS_K_PERCENT: Final[str] = "chk_stats_k_percent"
CHK_STATS_ON: Final[str] = "on"

# Check Stats - xwOBA (chk_stats_xwoba)
# Values: "on" to include, empty string to exclude
CHK_STATS_XWOBA: Final[str] = "chk_stats_xwoba"

# Check Stats - Metric 1 (metric_1)
# Values: Empty string or metric code
METRIC_1: Final[str] = "metric_1"

# ============================================================================
# Example Query Parameter Dictionary
# ============================================================================

# Example pitcher query parameters based on the provided URL
EXAMPLE_PITCHER_PARAMS: dict[str, str] = {
    HF_PITCH_TYPE: "",
    HF_AT_BAT_RESULT: "",
    HF_GAME_TYPE: f"{GAME_TYPE_REGULAR}|",
    HF_PITCH_RESULT: "",
    HF_ZONE: "",
    HF_STADIUM: "",
    HF_BATTED_BALL_LOCATION: "",
    HF_NEW_ZONES: "",
    HF_PULL: "",
    HF_COUNT: "",
    HF_SEASON: "2025|",
    HF_SITUATION: "",
    "player_type": PLAYER_TYPE_PITCHER,
    HF_OUTS: "",
    HOME_ROAD: "",
    PITCHER_THROWS: "",
    BATTER_STANDS: "",
    HF_SPECIAL_ATTRIBUTES: "",
    HF_EVENT_OUTS: "",
    HF_EVENT_RUNS: "",
    GAME_DATE_GT: "",
    GAME_DATE_LT: "",
    HF_MONTH: "",
    HF_TEAM: "",
    HF_OPPONENT: "",
    HF_RUNNER_ON: "",
    POSITION: "",
    HF_INFIELD: "",
    HF_OUTFIELD: "",
    HF_INNING: "",
    HF_BBT: "",
    HF_FLAG: f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|",
    METRIC_1: "",
    GROUP_BY: GROUP_BY_NAME,
    MIN_PITCHES: "0",
    MIN_RESULTS: "0",
    MIN_PLATE_APPEARANCES: "30",
    SORT_COLUMN: SORT_COL_XWOBA,
    PLAYER_EVENT_SORT: PLAYER_EVENT_SORT_RELEASE_SPEED,
    SORT_ORDER: SORT_ORDER_ASC,
    CHK_STATS_K_PERCENT: CHK_STATS_ON,
    CHK_STATS_XWOBA: CHK_STATS_ON,
}
