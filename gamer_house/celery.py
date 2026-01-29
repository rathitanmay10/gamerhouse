import os

from celery import Celery, Task
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gamer_house.settings")


class ContextTask(Task):
    """
    Custom Celery Task that propagates correlation_id from the context
    to the task headers (producer side) and from headers back to the
    context (consumer side).
    """

    def apply_async(self, args=None, kwargs=None, **options):
        # PRODUCER SIDE: Get correlation_id from context and add to headers
        from core.context import get_correlation_id

        correlation_id = get_correlation_id()

        # If no correlation ID (e.g. Beat task), generate one for the message
        # but don't set it in context to avoid "stale" IDs in long-running processes
        if not correlation_id:
            import uuid

            correlation_id = str(uuid.uuid4())

        headers = options.setdefault("headers", {})
        headers["X-Correlation-ID"] = correlation_id

        return super().apply_async(args, kwargs, **options)

    def __call__(self, *args, **kwargs):
        # CONSUMER SIDE: Get correlation_id from headers and set in context
        from core.context import set_correlation_id

        request = self.request
        correlation_id = getattr(request, "headers", {}).get("X-Correlation-ID")

        # If no correlation ID in headers (e.g. Beat task), get_correlation_id()
        # will typically return None, but our get_correlation_id implementation
        # auto-generates one effectively for the scope if missing.
        # However, to explicitly respect the header:
        if correlation_id:
            set_correlation_id(correlation_id)

        return super().__call__(*args, **kwargs)


app = Celery("gamer_house", task_cls=ContextTask)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "flush-expired-jwt-tokens": {
        "task": "core.tasks.flush_expired_jwt_tokens",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "polling-reconcile-task": {
        "task": "payments.tasks.polling_reconcile_task",
        "schedule": crontab(minute="*/5"),
    },
}
