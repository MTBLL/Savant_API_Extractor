# Agent Commands Reference

This project uses `uv` for dependency management and command execution. All commands should be run using `uv run` prefix.

## Basic Usage

### Extract All Data (Batters and Pitchers)
```bash
uv run savant_api_extractor
```

This will create separate files with timestamps:
- `savant_batters_YYYY_MM_DD_HHMM.json`
- `savant_pitchers_YYYY_MM_DD_HHMM.json`

Example output:
- `savant_batters_2026_01_03_1430.json`
- `savant_pitchers_2026_01_03_1430.json`

### Extract Batters Only
```bash
uv run python -m savant_api_extractor --type batters
```

This will create:
- `savant_batters_YYYY_MM_DD_HHMM.json`

### Extract Pitchers Only
```bash
uv run savant_api_extractor --type pitchers
```

This will create:
- `savant_pitchers_YYYY_MM_DD_HHMM.json`

## Advanced Options

### Specify Season
```bash
uv run savant_api_extractor --season 2025
```

### Custom Output Directory
```bash
uv run savant_api_extractor --output-dir ./data
```

Files will be created with the standardized naming convention:
- `savant_batters_YYYY_MM_DD_HHMM.json`
- `savant_pitchers_YYYY_MM_DD_HHMM.json`

### Threshold Options

Control minimum plate appearance requirements:

```bash
# Default: 30 PA for batters, 20 for pitchers
uv run savant_api_extractor --threshold default

# Wide: 50% of default (15/10)
uv run savant_api_extractor --threshold wide

# Open: No minimums
uv run savant_api_extractor --threshold open

# Spring Training: No minimums, spring training games only
uv run savant_api_extractor --threshold spring_training
```

## Combined Example

```bash
uv run python -m savant_api_extractor \
  --type all \
  --season 2025 \
  --threshold wide \
  --output-dir ./output
```

This will create (with current timestamp):
- `./output/savant_batters_2026_01_03_1430.json`
- `./output/savant_pitchers_2026_01_03_1430.json`

## Development Commands

### Run Tests
```bash
uv run pytest --cov --cov-report=term-missing -v
```

### Run Type Checking
```bash
uv run mypy savant_api_extractor
```

### Run Linting
```bash
uv run ruff check savant_api_extractor
```

### Format Code
```bash
uv run ruff format savant_api_extractor
```

## Notes

- All commands use `uv run` prefix to ensure proper dependency resolution
- When `--type all` is used, data is automatically sharded into separate pitcher and batter files
- Output files are in JSON format with 2-space indentation
- The tool creates the output directory if it doesn't exist
- Filenames follow the pattern: `savant_<position>_YYYY_MM_DD_HHMM.json`
  - `<position>` is either `batters` or `pitchers`
  - Timestamp format: Year_Month_Day_HourMinute (24-hour format)
  - Example: `savant_batters_2026_01_03_1430.json` = January 3rd, 2026 at 2:30 PM
