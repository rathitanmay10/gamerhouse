import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gamer_house.settings")

app = Celery("gamer_house")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "flush-expired-jwt-tokens": {
        "task": "core.tasks.flush_expired_jwt_tokens",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "polling-reconcile-task": {
        "task": "payments.tasks.polling_reconcile_task",
        "schedule": crontab(minute="*/15"),
    },
}
