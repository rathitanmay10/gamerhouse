from django.contrib import admin

from payments.models import Payment, Subscription, WebhookEvent

admin.site.register(Payment)
admin.site.register(Subscription)
admin.site.register(WebhookEvent)
