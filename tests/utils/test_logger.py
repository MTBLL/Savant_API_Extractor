"""Tests for the logger utility."""

import logging
from pathlib import Path

from savant_api_extractor.utils.logger import Logger


class TestLogger:
    """Test cases for the Logger class."""

    def test_logger_creation(self) -> None:
        """Test that a logger can be created."""
        logger = Logger("test_logger_creation")
        assert logger.logger is not None
        assert logger.logger.name == "test_logger_creation"

    def test_logger_levels(self) -> None:
        """Test that logger can log at different levels."""
        logger = Logger("test_logger_levels", log_level=logging.DEBUG)
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_logger_with_file(self, tmp_path: Path) -> None:
        """Test that logger can write to a file."""
        log_file = tmp_path / "test.log"
        logger = Logger("test_logger_with_file", log_file=log_file)
        logger.info("Test message")
        
        # Verify file was created and contains the message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
