"""
dashboard/utils/logger.py
--------------------------
Centralised application logger with rotating file handler.
Usage:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Something happened")
"""

import os
import logging
from logging.handlers import RotatingFileHandler

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LOG_DIR  = os.path.join(_BASE_DIR, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "grc_app.log")

_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.WARNING)   # silence third-party noise

_file_handler = RotatingFileHandler(
    _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
_file_handler.setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger wired to the rotating file handler."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(_file_handler)
        logger.setLevel(logging.DEBUG)
    return logger
