from django.shortcuts import render
from django.views import View


class ResetPasswordPageView(View):
    """
    Render the reset password page.

    This view is accessed via the link sent in the password reset email.
    The token is passed as a query parameter and embedded in the form.
    """

    def get(self, request):
        token = request.GET.get("token", "")
        return render(request, "users/reset_password.html", {"token": token})
