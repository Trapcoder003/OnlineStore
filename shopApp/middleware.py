from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
from django.conf import settings


# URL name prefixes that must stay public
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

# Path prefixes that must stay public (admin, static, media)
PUBLIC_PATH_PREFIXES = (
    settings.STATIC_URL,
    settings.MEDIA_URL,
    "/admin/",
    "/accounts/",
)


class LoginRequiredMiddleware:
    """
    Redirects unauthenticated users to LOGIN_URL for every page
    that isn't explicitly public.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        # Allow static / media / admin
        for prefix in PUBLIC_PATH_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # Allow explicitly public URL names
        try:
            match = resolve(path)
            if match.url_name in PUBLIC_URL_NAMES:
                return self.get_response(request)
        except Resolver404:
            pass

        # Otherwise — bounce to login with ?next=
        login_url = reverse(settings.LOGIN_URL)
        return redirect(f"{login_url}?next={path}")