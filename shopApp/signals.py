from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import TrackingHistory


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
    # (e.g., don't email when the internal tracking row is created manually for testing)
    if instance.status in ("pending", "failed"):
        return

    subject = f"Order {order.order_number} · {instance.get_status_display()}"
    message = (
        f"Hi {order.ship_name},\n\n"
        f"Your order {order.order_number} status is now: {instance.get_status_display()}.\n\n"
        f"{instance.note}\n\n"
        f"Total: KES {order.total}\n\n"
        f"Track your order anytime:\n"
        f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://trapcoder.pythonanywhere.com'}/track/{order.order_number}/\n\n"
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
        # Log, don't crash — the status update already succeeded
        print(f"❌ Tracking email failed for {order.order_number}: {e}")