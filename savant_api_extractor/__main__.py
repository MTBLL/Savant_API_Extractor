"""CLI entry point for Savant API Extractor."""

import json
from pathlib import Path

import click

from savant_api_extractor.runner.savant_runner import SavantRunner
from savant_api_extractor.utils.logger import Logger


@click.command()
@click.option(
    "--batter-params",
    type=click.Path(exists=True),
    help="Path to JSON file with batter query parameters",
)
@click.option(
    "--pitcher-params",
    type=click.Path(exists=True),
    help="Path to JSON file with pitcher query parameters",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default=".",
    help="Output directory for JSON files (default: current directory)",
)
@click.option(
    "--output-filename",
    default="savant_data",
    help="Output filename without extension (default: savant_data)",
)
@click.option(
    "--type",
    "extraction_type",
    type=click.Choice(["batters", "pitchers", "all"], case_sensitive=False),
    default="all",
    help="Type of data to extract (default: all)",
)
def main(
    batter_params: str | None,
    pitcher_params: str | None,
    output_dir: str,
    output_filename: str,
    extraction_type: str,
) -> None:
    """
    Extract statistics from Baseball Savant API.

    Query parameters should be provided as JSON files. Each file should contain
    a JSON object with the query parameters as key-value pairs.

    Example query params file:
    {
        "all": "true",
        "type": "details",
        "player_type": "batter"
    }
    """
    logger = Logger(f"{__name__}.main")
    logger.info("Starting Savant API extraction")

    # Load query parameters
    batter_query_params: dict | None = None
    pitcher_query_params: dict | None = None

    if batter_params:
        with open(batter_params, "r") as f:
            batter_query_params = json.load(f)
        logger.info(f"Loaded batter params from {batter_params}")

    if pitcher_params:
        with open(pitcher_params, "r") as f:
            pitcher_query_params = json.load(f)
        logger.info(f"Loaded pitcher params from {pitcher_params}")

    # Initialize runner
    runner = SavantRunner(output_dir=Path(output_dir))

    # Run extraction based on type
    try:
        if extraction_type.lower() == "batters":
            if not batter_query_params:
                logger.error("Batter params required for batter extraction")
                raise click.BadParameter("--batter-params required when type=batters")
            runner.run_batters(batter_query_params, output_filename)
        elif extraction_type.lower() == "pitchers":
            if not pitcher_query_params:
                logger.error("Pitcher params required for pitcher extraction")
                raise click.BadParameter("--pitcher-params required when type=pitchers")
            runner.run_pitchers(pitcher_query_params, output_filename)
        else:  # all
            runner.run_all(batter_query_params, pitcher_query_params, output_filename)

        logger.info("Extraction completed successfully")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()