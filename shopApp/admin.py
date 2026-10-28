from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import (
    Category, Product, Wishlist, Review,
    Order, OrderItem, TrackingHistory,
)


# ============================================================
# Simple registrations
# ============================================================
admin.site.register(Category)
admin.site.register(Wishlist)
admin.site.register(Review)


# ============================================================
# PRODUCT
# ============================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "price", "old_price",
        "stock", "is_featured", "sold_count",
    )
    list_editable = ("is_featured",)
    list_filter = ("is_featured", "category")
    search_fields = ("name", "brand")
    list_per_page = 30


# ============================================================
# ORDER
# ============================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product", "product_name", "product_slug",
        "unit_price", "qty", "line_total_display",
    )
    can_delete = False

    def line_total_display(self, obj):
        if obj.pk:
            return f"KES {obj.line_total:,.0f}"
        return "—"
    line_total_display.short_description = "Line total"


class TrackingHistoryInline(admin.TabularInline):
    model = TrackingHistory
    extra = 1
    fields = ("status", "note", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "created_at", "ship_name", "phone",
        "status_badge", "total", "pickup_station_name", "mpesa_receipt",
    )
    list_filter = ("status", "delivery_method", "created_at")
    search_fields = (
        "order_number", "phone", "email",
        "ship_name", "mpesa_receipt", "pickup_station_name",
    )
    date_hierarchy = "created_at"
    inlines = [OrderItemInline, TrackingHistoryInline]
    readonly_fields = (
        "order_number", "created_at", "paid_at",
        "shipped_at", "delivered_at",
        "mpesa_checkout_id", "mpesa_receipt",
    )
    list_per_page = 30

    fieldsets = (
        ("Order", {
            "fields": (
                "order_number", "status", "total",
                "created_at", "paid_at", "notes",
            ),
        }),
        ("Customer", {
            "fields": ("user", "email", "phone"),
        }),
        ("Shipping", {
            "fields": (
                "ship_name", "ship_phone",
                "ship_county", "ship_town", "ship_address",
                "delivery_method",
            ),
        }),
        ("Pickup station", {
            "fields": (
                "pickup_station_name", "pickup_station_code",
                "pickup_station_address", "estimated_pickup_date",
            ),
            "classes": ("collapse",),
        }),
        ("Money", {
            "fields": ("subtotal", "shipping_fee", "discount"),
        }),
        ("M-Pesa", {
            "fields": (
                "mpesa_checkout_id", "mpesa_receipt",
                "mpesa_phone", "mpesa_result_desc",
            ),
            "classes": ("collapse",),
        }),
    )

    def status_badge(self, obj):
        colors = {
            "pending":          "#ffc93c",
            "paid":             "#5fe3b5",
            "processing":       "#7b61ff",
            "shipped":          "#7b61ff",
            "ready_for_pickup": "#ffc93c",
            "picked_up":        "#5fe3b5",
            "failed":           "#ff6b9b",
            "cancelled":        "#888",
            "refunded":         "#ff77b1",
        }
        color = colors.get(obj.status, "#888")
        return format_html(
            '<span style="background:{};color:#14103a;padding:3px 10px;'
            'border-radius:99px;font-weight:700;font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = "Status"

    # --------------------------------------------------------
    # Bulk actions — each one creates a TrackingHistory entry,
    # which fires the signal that emails the customer
    # --------------------------------------------------------
    actions = [
        "mark_processing",
        "mark_shipped_to_pickup",
        "mark_ready_for_pickup",
        "mark_picked_up",
        "cancel_orders",
        "export_csv",
    ]

    @admin.action(description="⚙️ Mark as Processing")
    def mark_processing(self, request, queryset):
        n = 0
        for order in queryset:
            if order.status not in ("paid", "processing"):
                continue
            order.status = "processing"
            order.save(update_fields=["status"])
            TrackingHistory.objects.create(
                order=order,
                status="processing",
                note="We're preparing your order.",
            )
            n += 1
        self.message_user(request, f"{n} order(s) marked as processing.")

    @admin.action(description="🚚 Mark as Shipped to Pickup Station")
    def mark_shipped_to_pickup(self, request, queryset):
        n = 0
        for order in queryset:
            if order.status in ("shipped", "ready_for_pickup", "picked_up", "cancelled"):
                continue
            order.status = "shipped"
            order.shipped_at = timezone.now()
            order.save(update_fields=["status", "shipped_at"])
            station = order.pickup_station_name or "your selected pickup station"
            TrackingHistory.objects.create(
                order=order,
                status="shipped",
                note=f"Dispatched to {station}.",
            )
            n += 1
        self.message_user(request, f"{n} order(s) marked as shipped.")

    @admin.action(description="📦 Mark as Ready for Pickup")
    def mark_ready_for_pickup(self, request, queryset):
        n = 0
        for order in queryset:
            if order.status in ("ready_for_pickup", "picked_up", "cancelled"):
                continue
            order.status = "ready_for_pickup"
            order.save(update_fields=["status"])
            station = order.pickup_station_name or "your pickup station"
            TrackingHistory.objects.create(
                order=order,
                status="ready_for_pickup",
                note=(
                    f"Your order is ready for pickup at {station}. "
                    f"Bring your ID and order number {order.order_number}."
                ),
            )
            n += 1
        self.message_user(request, f"{n} order(s) marked as ready for pickup.")

    @admin.action(description="✅ Mark as Picked Up")
    def mark_picked_up(self, request, queryset):
        n = 0
        for order in queryset:
            if order.status == "picked_up":
                continue
            order.status = "picked_up"
            order.delivered_at = timezone.now()
            order.save(update_fields=["status", "delivered_at"])
            TrackingHistory.objects.create(
                order=order,
                status="picked_up",
                note="Collected by customer. Thank you for shopping with us!",
            )
            n += 1
        self.message_user(request, f"{n} order(s) marked as picked up.")

    @admin.action(description="❌ Cancel selected orders")
    def cancel_orders(self, request, queryset):
        n = queryset.exclude(status__in=("picked_up", "cancelled")).update(
            status="cancelled"
        )
        self.message_user(request, f"{n} order(s) cancelled.")

    @admin.action(description="📥 Export selected as CSV")
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Order", "Date", "Customer", "Phone",
            "Total", "Status", "Receipt", "Pickup station",
        ])
        for o in queryset:
            writer.writerow([
                o.order_number,
                o.created_at.strftime("%Y-%m-%d %H:%M"),
                o.ship_name,
                o.phone,
                o.total,
                o.status,
                o.mpesa_receipt,
                o.pickup_station_name,
            ])
        return response


# ============================================================
# TRACKING HISTORY (optional direct admin — inlines above
# are the main way you'll use this)
# ============================================================
@admin.register(TrackingHistory)
class TrackingHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "created_at", "note_preview")
    list_filter = ("status", "created_at")
    search_fields = ("order__order_number", "note")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50

    def note_preview(self, obj):
        if not obj.note:
            return "—"
        return obj.note[:60] + ("…" if len(obj.note) > 60 else "")
    note_preview.short_description = "Note"