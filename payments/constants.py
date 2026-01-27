"""
Payment-related constants and configuration.
"""

# Premium Subscription Pricing
PREMIUM_PRICE_INR = 499  # Amount in INR
PREMIUM_PRICE_PAISE = PREMIUM_PRICE_INR * 100  # Amount in paise for Razorpay

# Payment Configuration
PAYMENT_CURRENCY = "INR"
PAYMENT_CAPTURE_MODE = 1  # Auto-capture

# Polling Configuration
POLLING_MAX_RETRIES = 10  # Maximum number of polling attempts
POLLING_BACKOFF_BASE = 300  # Base backoff in seconds (5 minutes)
POLLING_BACKOFF_MAX = 3600  # Maximum backoff in seconds (1 hour)

# Webhook Configuration
WEBHOOK_TIMEOUT_SECONDS = 30
