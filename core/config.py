from datetime import timedelta

# Auth / JWT
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=1)

# Pagination
MAX_PAGE_SIZE = 100
PAGE_SIZE = 10
