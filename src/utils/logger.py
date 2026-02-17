import logging
import sys
from .config import Config

def setup_logger(name: str = "credit_eligibility"):
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger
