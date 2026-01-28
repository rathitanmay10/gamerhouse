from datetime import timedelta

# Auth / JWT
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=1)

# Pagination
MAX_PAGE_SIZE = 100
PAGE_SIZE = 10

# Time-to-live values (in seconds)
EMAIL_VERIFY_TTL = 60 * 60
PASSWORD_RESET_TTL = 60 * 30
LOGIN_OTP_TTL = 60 * 10

# OTP security limits
MAX_OTP_ATTEMPTS = 5

MAX_FREE_USER_GAMES = 5

# Celery Task Configuration
EMAIL_TASK_RETRY_BACKOFF = 5  # Retry backoff for email tasks (seconds)
EMAIL_TASK_MAX_RETRIES = 3  # Max retries for email tasks
CORE_TASK_MAX_RETRIES = 3  # Max retries for core tasks
