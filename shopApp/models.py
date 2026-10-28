from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets



class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    emoji = models.CharField(max_length=4, blank=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    brand = models.CharField(max_length=100, blank=True)

    # Featured products (used by homepage "Featured" strip)
    is_featured = models.BooleanField(default=False)

    # Sales tracking (used by homepage "Best Sellers" strip)
    sold_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    image = models.ImageField(upload_to="reviews/images/", blank=True, null=True)
    video = models.FileField(upload_to="reviews/videos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending",   "Pending payment"),
        ("paid",      "Paid"),
        ("failed",    "Payment failed"),
        ("shipped",   "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded",  "Refunded"),
    ]

    DELIVERY_CHOICES = [
        ("pickup",   "Pickup at store (Free)"),
        ("standard", "Standard delivery (KES 300)"),
        ("express",  "Express delivery (KES 500)"),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Shipping
    ship_name = models.CharField(max_length=120)
    ship_phone = models.CharField(max_length=20)
    ship_county = models.CharField(max_length=80)
    ship_town = models.CharField(max_length=80)
    ship_address = models.TextField(help_text="Building, street, landmark")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default="standard")

    # Money (all snapshotted at purchase time)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True, help_text="Internal notes")

    # M-Pesa
    mpesa_checkout_id = models.CharField(max_length=80, blank=True, db_index=True)
    mpesa_receipt = models.CharField(max_length=40, blank=True)
    mpesa_phone = models.CharField(max_length=20, blank=True)
    mpesa_result_desc = models.CharField(max_length=200, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Pickup station details
    pickup_station_name = models.CharField(max_length=120, blank=True)
    pickup_station_code = models.CharField(max_length=40, blank=True)
    pickup_station_address = models.TextField(blank=True)

    # Tracking status (expand your existing STATUS_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending payment'),
            ('paid', 'Paid'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped to Pickup Station'),
            ('ready_for_pickup', 'Ready for Pickup'),
            ('picked_up', 'Picked Up'),
            ('failed', 'Payment Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    # Optional: estimated delivery/pickup date
    estimated_pickup_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["mpesa_checkout_id"]),
        ]

    def __str__(self):
        return f"{self.order_number} · {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            year = timezone.now().year
            for _ in range(20):  # safety loop
                candidate = f"ESH-{year}-{secrets.randbelow(900000) + 100000}"
                if not Order.objects.filter(order_number=candidate).exists():
                    self.order_number = candidate
                    break
            else:
                raise RuntimeError("Could not generate unique order number")
        super().save(*args, **kwargs)

    def mark_paid(self, receipt="", phone="", description=""):
        self.status = "paid"
        self.paid_at = timezone.now()
        self.mpesa_receipt = receipt
        self.mpesa_phone = phone
        self.mpesa_result_desc = description
        self.save()

    @property
    def item_count(self):
        return sum(i.qty for i in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)

    # Snapshots (survive product deletion / rename / price change)
    product_name = models.CharField(max_length=200)
    product_slug = models.SlugField(max_length=200, blank=True)
    product_image_url = models.CharField(max_length=300, blank=True)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.qty} × {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.qty

class TrackingHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=20)  # matches Order.status
    note = models.TextField(blank=True)      # e.g., "Arrived at Nairobi CBD pickup point"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.created_at}"