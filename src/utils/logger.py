"""
Logger
Application logging utilities
"""

import logging
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import LOG_FILE, DATA_DIR


def setup_logger(name="TikTokDownloader", level=logging.INFO):
    """
    Setup application logger
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Logger: Configured logger instance
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name="TikTokDownloader"):
    """
    Get existing logger instance
    
    Args:
        name: Logger name
    
    Returns:
        Logger: Logger instance
    """
    return logging.getLogger(name)
