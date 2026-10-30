from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserProfile


from .models import TrackingHistory, Order


# Status display mapping — mirrors Order.STATUS_CHOICES
STATUS_LABELS = dict(Order.STATUS_CHOICES)


@receiver(post_save, sender=TrackingHistory)
def notify_customer_of_status_change(sender, instance, created, **kwargs):
    """
    Send an email whenever a TrackingHistory entry is created.
    Fires once per new row (not on updates), so no duplicate emails.
    """
    if not created:
        return

    order = instance.order

    # Skip notification for statuses you don't want to email about
    if instance.status in ("pending", "failed"):
        return

    # Manual label lookup — TrackingHistory has no choices, so no get_status_display()
    label = STATUS_LABELS.get(instance.status, instance.status.replace("_", " ").title())

    subject = f"Order {order.order_number} · {label}"
    site_url = getattr(settings, "SITE_URL", "https://trapcoder.pythonanywhere.com")
    message = (
        f"Hi {order.ship_name},\n\n"
        f"Your order {order.order_number} is now: {label}.\n\n"
        f"{instance.note}\n\n"
        f"Total: KES {order.total}\n\n"
        f"Track your order anytime:\n"
        f"{site_url}/track/{order.order_number}/\n\n"
        f"— E-Shop"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=False,
        )
        print(f"📧 Tracking email sent to {order.email} · status={instance.status}")
    except Exception as e:
        print(f"❌ Tracking email failed for {order.order_number}: {e}")
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile on signup. Never blocks save."""
    if created:
        UserProfile.objects.get_or_create(user=instance)