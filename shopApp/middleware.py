from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
from django.conf import settings


# URL names that MUST stay public for allauth to work
PUBLIC_URL_NAMES = {
    "account_login",
    "account_signup",
    "account_reset_password",
    "account_reset_password_done",
    "account_reset_password_from_key",
    "account_reset_password_from_key_done",
    "account_logout",
    "account_confirm_email",
    "account_email_verification_sent",
    "contact",
    "contact_success",
    "faq",
    "privacy",
    "terms",
    "shipping",
}

# Path prefixes that MUST stay public (static files, admin, auth pages)
PUBLIC_PATH_PREFIXES = (
    settings.STATIC_URL,   # Usually "/static/"
    settings.MEDIA_URL,    # Usually "/media/"
    "/admin/",             # Django admin panel
    "/accounts/",          # Allauth login/signup/reset pages
)


class LoginRequiredMiddleware:
    """
    Forces unauthenticated users to the login page for ALL pages
    except the ones listed in the public sets above.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. If the user is already logged in, let them see everything
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        # 2. Allow static files, media, admin, and /accounts/ paths
        for prefix in PUBLIC_PATH_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # 3. Allow explicitly public URL names
        try:
            match = resolve(path)
            if match.url_name in PUBLIC_URL_NAMES:
                return self.get_response(request)
        except Resolver404:
            pass

        # 4. Block everything else and send them to login
        login_url = reverse(settings.LOGIN_URL)
        return redirect(f"{login_url}?next={path}")