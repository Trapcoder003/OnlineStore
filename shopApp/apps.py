from django.apps import AppConfig


class ShopappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shopApp"

    def ready(self):
        # 🔑 This line loads signals.py when Django starts
        import shopApp.signals  # noqa: F401
    