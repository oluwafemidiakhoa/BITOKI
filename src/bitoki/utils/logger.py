"""Logging configuration for the trading strategy."""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(config: dict) -> None:
    """
    Setup logger with configuration.

    Args:
        config: Dictionary with logging configuration
    """
    # Remove default handler
    logger.remove()

    # Get log level
    log_level = config.get('level', 'INFO')

    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # File handler if enabled
    if config.get('to_file', False):
        log_path = Path(config.get('file_path', 'logs/strategy.log'))
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=log_level,
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )

    logger.info(f"Logger initialized with level: {log_level}")


def get_logger():
    """Get configured logger instance."""
    return logger
