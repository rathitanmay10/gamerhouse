import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from core.constants import (
    EMAIL_TASK_MAX_RETRIES,
    EMAIL_TASK_RETRY_BACKOFF,
    EMAIL_VERIFY_TTL,
    LOGIN_OTP_TTL,
    PASSWORD_RESET_TTL,
)
from core.context import get_correlation_id
from users.models import User

logger = logging.getLogger(__name__)
correlation_id = get_correlation_id()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=EMAIL_TASK_RETRY_BACKOFF,
    retry_kwargs={"max_retries": EMAIL_TASK_MAX_RETRIES},
)
def send_verification_email(self, email, token):
    if settings.DEBUG:
        logger.info(
            "VERIFY EMAIL → email=%s token=%s",
            email,
            token,
            extra={
                "correlation_id": correlation_id,
            },
        )

    verify_url = f"{settings.FRONTEND_URL}verify-token/?token={token}"
    expiry_minutes = EMAIL_VERIFY_TTL // 60

    send_mail(
        subject="Verify your email",
        message=f"Click the link to verify your account:\n\n{verify_url}\n\nThis link expires in {expiry_minutes} minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=EMAIL_TASK_RETRY_BACKOFF,
    retry_kwargs={"max_retries": EMAIL_TASK_MAX_RETRIES},
)
def send_password_reset_email(self, email, token):
    reset_url = f"{settings.FRONTEND_URL}reset-password/?token={token}"
    expiry_minutes = PASSWORD_RESET_TTL // 60

    if settings.DEBUG:
        logger.info(
            "PASSWORD RESET → email=%s token=%s",
            email,
            token,
            extra={
                "correlation_id": correlation_id,
            },
        )

    send_mail(
        subject="Reset your password",
        message=f"Reset your password using the link below:\n\n{reset_url}\n\nThis link expires in {expiry_minutes} minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=EMAIL_TASK_RETRY_BACKOFF,
    retry_kwargs={"max_retries": EMAIL_TASK_MAX_RETRIES},
)
def send_otp_email(self, email, otp):
    expiry_minutes = LOGIN_OTP_TTL // 60

    if settings.DEBUG:
        logger.info("VERIFY EMAIL LOGIN → email=%s otp=%s", email, otp)

    send_mail(
        subject="OTP for login",
        message=f"OTP for login is \n{otp}\n\nThis otp expires in {expiry_minutes} minutes.",
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
@transaction.atomic
def soft_delete_user_data(self, user_id):
    from user_games.models import UserGameNote

    UserGameNote.objects.filter(user_game__user_id=user_id).update(
        deleted_at=timezone.now()
    )

    user = User.all_objects.get(id=user_id)
    user.user_games.all().update(deleted_at=timezone.now())