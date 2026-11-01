from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# Custom login view — redirects staff straight to /staff/
from shopApp.views import StaffAwareLoginView

urlpatterns = [
    # 1. SECURE ADMIN: Only you know this URL
    path("trapcoder-master-panel/", admin.site.urls),

    # 2. OVERRIDE: Login page — staff go straight to /staff/, customers to home
    path(
        "accounts/login/",
        StaffAwareLoginView.as_view(),
        name="account_login",
    ),

    # 3. STANDARD ALLAUTH URLS
    #    (Handles password reset including /accounts/password/reset/key/<uidb36>-<key>/)
    path("accounts/", include("allauth.urls")),

    # 4. STAFF BACK-OFFICE (must come BEFORE the customer catch-all)
    path("staff/", include("shopApp.staff_urls")),

    # 5. YOUR APP URLS (catch-all — must stay LAST)
    path("", include("shopApp.urls")),
]

# Media only — static is handled automatically by
# django.contrib.staticfiles in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)