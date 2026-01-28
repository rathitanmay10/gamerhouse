import os
from pathlib import Path

from django.conf import settings

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_ENABLED = os.getenv("LOG_FILE_ENABLED", "True") == "True"


def get_logging_config():
    BASE_DIR = Path(settings.BASE_DIR)
    LOGS_DIR = BASE_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)


    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": LOG_LEVEL,
            },
            "middleware_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(LOGS_DIR / "server.log"),
                "maxBytes": 1024 * 200,  # 200 KB
                "backupCount": 1,
                "formatter": "json",
                "encoding": "utf-8",
                "level": "NOTSET",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
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
            "request_logger": {
                "handlers": ["middleware_file", "console"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }
