from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import the custom view we created to fix the password reset link
from shopApp.views import CustomPasswordResetFromKeyView

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # 1. OVERRIDE: This custom route must be placed BEFORE the allauth include
    path(
        "accounts/password/reset/key/<uidb36>-<key>/", 
        CustomPasswordResetFromKeyView.as_view(), 
        name="account_reset_password_from_key"
    ),
    
    # 2. STANDARD ALLAUTH URLS
    path("accounts/", include("allauth.urls")),
    
    # 3. YOUR APP URLS
    path("", include("shopApp.urls")),
]

# Media only — static is handled automatically by
# django.contrib.staticfiles in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)