from celery import shared_task
from django.core.management import call_command


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def flush_expired_jwt_tokens(self):
    call_command("flushexpiredtokens")
