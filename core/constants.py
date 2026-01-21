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
