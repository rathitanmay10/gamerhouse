import os
from datetime import datetime
from pathlib import Path

from django.conf import settings

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_ENABLED = os.getenv("LOG_FILE_ENABLED", "True") == "True"


def get_logging_config():
    BASE_DIR = Path(settings.BASE_DIR)
    LOGS_DIR = BASE_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)

    TODAY_LOG_FILE = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

    return {
        "version": 1,
        # CRUCIAL → keep Django's default logging untouched
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            # Django default console — DO NOT TOUCH
            "console": {
                "class": "logging.StreamHandler",
                "level": LOG_LEVEL,
            },
            # Only middleware writes to file
            "middleware_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": str(TODAY_LOG_FILE),
                "when": "midnight",
                "interval": 1,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
                "level": LOG_LEVEL,
            },
        },
        "loggers": {
            # Django default → console only
            "django": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            # Django request (404, error) → default behavior
            "django.request": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
            "django.views": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
            "django.server": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
            # Your middleware → file only
            "request_logger": {
                "handlers": ["middleware_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
        },
        # Default console behavior
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }
