from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# Import the custom views we created
from shopApp.views import CustomPasswordResetFromKeyView, StaffAwareLoginView

urlpatterns = [
    # 1. SECURE ADMIN: Only you know this URL
    path("trapcoder-master-panel/", admin.site.urls),

    # 2. OVERRIDE: This custom route must be placed BEFORE the allauth include
    path(
        "accounts/password/reset/key/<uidb36>-<key>/",
        CustomPasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key"
    ),

    # 3. OVERRIDE: Login page — staff go straight to /staff/, customers to home
    path(
        "accounts/login/",
        StaffAwareLoginView.as_view(),
        name="account_login",
    ),

    # 4. STANDARD ALLAUTH URLS
    path("accounts/", include("allauth.urls")),

    # 5. STAFF BACK-OFFICE (must come BEFORE the customer catch-all)
    path("staff/", include("shopApp.staff_urls")),

    # 6. YOUR APP URLS (catch-all — must stay LAST)
    path("", include("shopApp.urls")),
]

# Media only — static is handled automatically by
# django.contrib.staticfiles in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)