import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def send_verification_email(self, email, token):
    if settings.DEBUG:
        logger.info("VERIFY EMAIL → email=%s token=%s", email, token)

    verify_url = f"{settings.FRONTEND_URL}verify-token/?token={token}"

    send_mail(
        subject="Verify your email",
        message=f"Click the link to verify your account:\n\n{verify_url}\n\nThis link expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def send_password_reset_email(self, email, token):
    reset_url = f"{settings.FRONTEND_URL}reset-password/?token={token}"

    if settings.DEBUG:
        logger.info("PASSWORD RESET → email=%s token=%s", email, token)

    send_mail(
        subject="Reset your password",
        message=f"Reset your password using the link below:\n\n{reset_url}\n\nThis link expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def send_otp_email(self, email, otp):
    if settings.DEBUG:
        logger.info("VERIFY EMAIL LOGIN → email=%s otp=%s", email, otp)

    send_mail(
        subject="OTP for login",
        message=f"OTP for login is \n{otp}\n\nThis otp expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
