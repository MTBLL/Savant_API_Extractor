"""Logger utility for the Savant API Extractor."""

import logging
import sys
from pathlib import Path
from typing import Optional


class Logger:
    """Logger class that creates a logger instance for each class."""

    def __init__(
        self,
        name: str,
        log_level: int = logging.INFO,
        log_file: Optional[Path] = None,
    ) -> None:
        """
        Initialize a logger instance.

        Args:
            name: Name of the logger (typically __name__ or class name)
            log_level: Logging level (default: INFO)
            log_file: Optional path to log file
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # Prevent duplicate handlers if logger already exists
        if self.logger.handlers:
            return

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
