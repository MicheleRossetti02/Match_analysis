"""
Logging configuration for the application
"""
import sys
import os
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings


def setup_logger():
    """Configure loguru logger"""
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL
    )
    
    # Add file logger
    os.makedirs("logs", exist_ok=True)
    logger.add(
        settings.LOG_FILE,
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=settings.LOG_LEVEL
    )
    
    return logger


# Initialize logger
app_logger = setup_logger()


if __name__ == "__main__":
    # Test logger
    app_logger.info("Logger initialized successfully")
    app_logger.debug("This is a debug message")
    app_logger.warning("This is a warning")
    app_logger.error("This is an error")
    app_logger.success("This is a success message")
