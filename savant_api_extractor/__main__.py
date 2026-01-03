"""CLI entry point for Savant API Extractor."""

from pathlib import Path

import click

from savant_api_extractor.runner.savant_runner import SavantRunner
from savant_api_extractor.utils.logger import Logger
from savant_api_extractor.utils.thresholds import ThresholdType


@click.command()
@click.option(
    "--threshold",
    type=click.Choice(
        ["default", "wide", "open", "spring_training"], case_sensitive=False
    ),
    default="default",
    help=(
        "Threshold type for minimum plate appearances. "
        "default: 30 PA for batters, 20 for pitchers. "
        "wide: 50% of default (15/10). "
        "open: no minimums. "
        "spring_training: no minimums, spring training games only."
    ),
)
@click.option(
    "--season",
    type=str,
    default="2025",
    help="Season year (e.g., '2025'). If not provided, uses API defaults.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default=".",
    help="Output directory for JSON files (default: current directory)",
)
@click.option(
    "--type",
    "extraction_type",
    type=click.Choice(["batters", "pitchers", "all"], case_sensitive=False),
    default="all",
    help="Type of data to extract (default: all)",
)
def main(
    threshold: str,
    season: str,
    output_dir: str,
    extraction_type: str,
) -> None:
    """
    Extract statistics from Baseball Savant API.

    The controller automatically generates query parameters based
    on threshold options.
    This is useful for early season when players haven't reached
    normal minimums yet.
    """
    logger = Logger(f"{__name__}.main")
    logger.info("Starting Savant API extraction")

    # Convert threshold string to enum
    threshold_type = ThresholdType(threshold.lower())

    # Initialize runner
    runner = SavantRunner(
        season, extraction_type, threshold_type, output_dir=Path(output_dir)
        )

    # Run extraction based on type
    try:
        _ = runner.run()

        logger.info("Extraction completed successfully")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
