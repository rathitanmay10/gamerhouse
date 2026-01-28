from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from payments.constants import PREMIUM_PRICE_INR


class PremiumCheckoutPage(View):
    def get(self, request):
        return render(
            request, "payments/checkout.html", {"premium_price": PREMIUM_PRICE_INR}
        )


@csrf_exempt
def payment_callback(request):
    return render(request, "payments/callback.html")
