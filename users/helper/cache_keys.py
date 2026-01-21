def verify_email_key(email: str) -> str:
    return f"verify:email:{email.lower()}"


def verify_token_key(token: str) -> str:
    return f"verify:token:{token}"


def reset_email_key(email: str) -> str:
    return f"reset:email:{email.lower()}"


def reset_token_key(token: str) -> str:
    return f"reset:token:{token}"


def login_otp_key(email: str) -> str:
    return f"login:otp:{email.lower()}"


def login_otp_attempts_key(email: str) -> str:
    """
    Tracks OTP verification attempts for a single OTP per email.
    TTL should match OTP TTL.
    """
    return f"login:otp:attempts:{email.lower()}"
