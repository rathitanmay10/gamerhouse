import logging

from celery import shared_task
from django.core.management import call_command

from core.constants import CORE_TASK_MAX_RETRIES
from core.context import get_correlation_id

logger = logging.getLogger(__name__)


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

    logger.info(
        "Successfully flushed expired JWT tokens",
        extra={"correlation_id": get_correlation_id()},
    )
