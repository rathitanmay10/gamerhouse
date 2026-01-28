from celery import shared_task
from django.core.management import call_command

from core.constants import CORE_TASK_MAX_RETRIES


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": CORE_TASK_MAX_RETRIES},
)
def flush_expired_jwt_tokens(self):
    """
    Flushes expired JWT tokens.
    """
    call_command("flushexpiredtokens")
