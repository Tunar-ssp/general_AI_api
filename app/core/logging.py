import logging
import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure loguru logger
config = {
    "handlers": [
        {
            "sink": sys.stdout,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "level": settings.LOG_LEVEL,
        },
        {
            "sink": log_dir / "api_manager.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            "level": settings.LOG_LEVEL,
            "rotation": "10 MB",
            "retention": "1 week",
        },
    ],
}

# Class to intercept standard logging and redirect to loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    # Remove all handlers from the root logger
    logging.root.handlers = []
    
    # Configure loguru with our settings
    logger.configure(**config)
    
    # Intercept standard logging messages
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Update logging levels for various libraries
    for logger_name in ("uvicorn", "uvicorn.error", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        
    return logger