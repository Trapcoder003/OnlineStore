from django.contrib import admin
from .models import Category, Product, Wishlist, Review
from .models import Category, Product, Wishlist, Review, Order, OrderItem

admin.site.register(Category)
admin.site.register(Wishlist)
admin.site.register(Review)


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

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "qty")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "created_at", "ship_name", "phone",
        "status_badge", "total", "mpesa_receipt",
    )
    list_filter = ("status", "delivery_method", "created_at")
    search_fields = ("order_number", "phone", "email", "ship_name", "mpesa_receipt")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    readonly_fields = ("order_number", "created_at", "paid_at", "mpesa_checkout_id", "mpesa_receipt")
    list_per_page = 30
    actions = ["mark_shipped", "mark_delivered", "mark_cancelled", "export_csv"]

    fieldsets = (
        ("Order", {"fields": ("order_number", "status", "total", "created_at", "paid_at", "notes")}),
        ("Customer", {"fields": ("user", "email", "phone")}),
        ("Shipping", {"fields": ("ship_name", "ship_phone", "ship_county", "ship_town", "ship_address", "delivery_method")}),
        ("Money", {"fields": ("subtotal", "shipping_fee", "discount")}),
        ("M-Pesa", {"fields": ("mpesa_checkout_id", "mpesa_receipt", "mpesa_phone", "mpesa_result_desc")}),
    )

    def status_badge(self, obj):
        colors = {
            "pending":   "#ffc93c",
            "paid":      "#5fe3b5",
            "failed":    "#ff6b9b",
            "shipped":   "#7b61ff",
            "delivered": "#5fe3b5",
            "cancelled": "#888",
            "refunded":  "#ff77b1",
        }
        color = colors.get(obj.status, "#888")
        return format_html(
            '<span style="background:{};color:#14103a;padding:3px 10px;border-radius:99px;'
            'font-weight:700;font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = "Status"

    @admin.action(description="📦 Mark as Shipped")
    def mark_shipped(self, request, queryset):
        from django.utils import timezone
        n = queryset.filter(status="paid").update(status="shipped", shipped_at=timezone.now())
        self.message_user(request, f"{n} order(s) marked as shipped.")

    @admin.action(description="✅ Mark as Delivered")
    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        n = queryset.update(status="delivered", delivered_at=timezone.now())
        self.message_user(request, f"{n} order(s) marked as delivered.")

    @admin.action(description="❌ Cancel selected orders")
    def mark_cancelled(self, request, queryset):
        n = queryset.update(status="cancelled")
        self.message_user(request, f"{n} order(s) cancelled.")

    @admin.action(description="📥 Export selected as CSV")
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(["Order", "Date", "Customer", "Phone", "Total", "Status", "Receipt"])
        for o in queryset:
            writer.writerow([o.order_number, o.created_at.strftime("%Y-%m-%d %H:%M"),
                             o.ship_name, o.phone, o.total, o.status, o.mpesa_receipt])
        return response