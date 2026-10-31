from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages
from django.shortcuts import resolve_url
from django.urls import reverse

class NoAutoLoginAfterSignupAdapter(DefaultAccountAdapter):
    """
    Prevent allauth from logging the user in automatically right after signup.
    User must visit the login page and authenticate manually.

    Also prevents auto-login after email confirmation and password reset.
    """

    def login(self, request, user):
        # Skip auto-login only when the call comes from the signup view.
        match = getattr(request, "resolver_match", None)
        if match and match.url_name == "account_signup":
            messages.success(
                request,
                "Your account was created successfully. Please log in to continue.",
            )
            return
        return super().login(request, user)

    def get_signup_redirect_url(self, request):
        # After successful signup, send the user to the login page.
        return resolve_url("account_login")

    def get_login_redirect_url(self, request):
        """
        Staff users land on /staff/ dashboard after login.
        Everyone else lands on the normal LOGIN_REDIRECT_URL ("home").
        """
        if request.user.is_authenticated and request.user.is_staff:
            return reverse("staff:dashboard")
        return super().get_login_redirect_url(request)
