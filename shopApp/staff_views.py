from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Q, Count, Max
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Order, Product, TrackingHistory, ORDER_STATUS_CHOICES
from .staff_forms import ProductForm



# ============================================================
# DASHBOARD
# ============================================================

@staff_member_required(login_url="account_login")
def dashboard(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    paid_today = Order.objects.filter(status="paid", paid_at__gte=today_start)
    paid_week = Order.objects.filter(status="paid", paid_at__gte=week_start)

    revenue_today = paid_today.aggregate(total=Sum("total"))["total"] or 0
    revenue_week = paid_week.aggregate(total=Sum("total"))["total"] or 0

    pending_orders = Order.objects.filter(status="pending").count()

    # Hide cancelled orders from dashboard 2 minutes after cancellation
    cancelled_cutoff = now - timedelta(minutes=2)
    recent_orders = (
        Order.objects
        .exclude(status__in=["pending", "failed"])
        .exclude(
            Q(status="cancelled") & (
                Q(cancelled_at__isnull=True) |
                Q(cancelled_at__lt=cancelled_cutoff)
            )
        )
        .order_by("-id")[:10]
    )    
    low_stock = Product.objects.filter(stock__lt=5, stock__gt=0).order_by("stock")[:8]
    out_of_stock = Product.objects.filter(stock=0).order_by("name")[:8]

    return render(request, "staff/dashboard.html", {
        "revenue_today": revenue_today,
        "revenue_week": revenue_week,
        "orders_today": paid_today.count(),
        "orders_week": paid_week.count(),
        "pending_orders": pending_orders,
        "recent_orders": recent_orders,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
    })


# ============================================================
# PRODUCTS
# ============================================================

@staff_member_required(login_url="account_login")
def products_list(request):
    filter_type = request.GET.get("filter", "all")
    q = request.GET.get("q", "").strip()

    products = Product.objects.select_related("category").order_by("-id")

    if filter_type == "low":
        products = products.filter(stock__lt=5, stock__gt=0)
    elif filter_type == "out":
        products = products.filter(stock=0)

    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(slug__icontains=q) | Q(category__name__icontains=q)
        )

    paginator = Paginator(products, 30)
    products_page = paginator.get_page(request.GET.get("page", 1))

    return render(request, "staff/products.html", {
        "products": products_page,
        "paginator": paginator,
        "filter_type": filter_type,
        "q": q,
        "total_count": Product.objects.count(),
        "low_count": Product.objects.filter(stock__lt=5, stock__gt=0).count(),
        "out_count": Product.objects.filter(stock=0).count(),
    })


@staff_member_required(login_url="account_login")
@require_POST
def product_stock_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    try:
        new_stock = int(request.POST.get("stock", product.stock))
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "Invalid stock value"}, status=400)

    if new_stock < 0:
        return JsonResponse({"ok": False, "error": "Stock cannot be negative"}, status=400)

    old_stock = product.stock
    product.stock = new_stock
    product.save(update_fields=["stock"])

    return JsonResponse({
        "ok": True,
        "product_id": product.id,
        "old_stock": old_stock,
        "new_stock": product.stock,
        "message": f"{product.name}: stock {old_stock} → {product.stock}",
    })


@staff_member_required(login_url="account_login")
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"✅ Product '{product.name}' created.")
            return redirect("staff:products")
    else:
        form = ProductForm()

    return render(request, "staff/product_form.html", {
        "form": form,
        "is_edit": False,
    })


@staff_member_required(login_url="account_login")
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Product '{product.name}' updated.")
            return redirect("staff:products")
    else:
        form = ProductForm(instance=product)

    return render(request, "staff/product_form.html", {
        "form": form,
        "product": product,
        "is_edit": True,
    })


@staff_member_required(login_url="account_login")
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"🗑️ Product '{name}' deleted.")
    return redirect("staff:products")


# ============================================================
# ORDERS
# ============================================================

NEXT_STATUS = {
    "paid": "processing",
    "processing": "shipped",
    "shipped": "ready_for_pickup",
    "ready_for_pickup": "picked_up",
}

STATUS_DISPLAY = {
    "paid": "Paid",
    "processing": "Processing",
    "shipped": "Shipped",
    "ready_for_pickup": "Ready for Pickup",
    "picked_up": "Picked Up",
    "cancelled": "Cancelled",
    "failed": "Failed",
    "refunded": "Refunded",
}

# Which statuses staff can set FROM each current status
VALID_STATUS_TRANSITIONS = {
    "pending": ["paid", "cancelled", "failed"],
    "paid": ["processing", "cancelled", "refunded"],
    "processing": ["shipped", "cancelled", "refunded"],
    "shipped": ["ready_for_pickup", "cancelled"],
    "ready_for_pickup": ["picked_up", "cancelled"],
    "picked_up": ["refunded"],
    "failed": ["pending", "cancelled"],
    "cancelled": [],
    "refunded": [],
}

STATUS_NOTES = {
    "pending": "Order set back to pending by staff.",
    "paid": "Payment confirmed manually by staff.",
    "processing": "Order is confirmed and being prepared.",
    "shipped": "Dispatched to pickup station.",
    "ready_for_pickup": "Ready for pickup.",
    "picked_up": "Collected. Thank you for shopping with us!",
    "cancelled": "Order cancelled by staff.",
    "failed": "Marked as failed by staff.",
    "refunded": "Refund issued by staff.",
}


@staff_member_required(login_url="account_login")
def orders_list(request):
    filter_type = request.GET.get("status", "active")
    q = request.GET.get("q", "").strip()

    orders = Order.objects.select_related("user").prefetch_related("items").order_by("-id")

    if filter_type == "active":
        orders = orders.exclude(status__in=["picked_up", "cancelled", "failed", "refunded"])
    elif filter_type != "all":
        orders = orders.filter(status=filter_type)

    if q:
        orders = orders.filter(
            Q(order_number__icontains=q)
            | Q(phone__icontains=q)
            | Q(email__icontains=q)
            | Q(ship_name__icontains=q)
        )

    paginator = Paginator(orders, 30)
    orders_page = paginator.get_page(request.GET.get("page", 1))

    status_counts = dict(
        Order.objects.values("status").annotate(c=Count("id")).values_list("status", "c")
    )

    return render(request, "staff/orders.html", {
        "orders": orders_page,
        "paginator": paginator,
        "filter_type": filter_type,
        "q": q,
        "status_counts": status_counts,
        "total_orders": Order.objects.count(),
    })


@staff_member_required(login_url="account_login")
def order_detail(request, number):
    order = get_object_or_404(Order, order_number=number)
    history = order.tracking_history.all()

    can_advance = order.status in NEXT_STATUS and order.paid_at
    next_status = NEXT_STATUS.get(order.status) if can_advance else None

    # Build the dropdown list of statuses staff can set from the current status
    allowed_keys = VALID_STATUS_TRANSITIONS.get(order.status, [])
    status_dict = dict(ORDER_STATUS_CHOICES)
    available_statuses = [(s, status_dict[s]) for s in allowed_keys if s in status_dict]

    return render(request, "staff/order_detail.html", {
        "order": order,
        "history": history,
        "can_advance": can_advance,
        "next_status": next_status,
        "next_status_display": STATUS_DISPLAY.get(next_status, next_status),
        "available_statuses": available_statuses,
    })


@staff_member_required(login_url="account_login")
@require_POST
def order_advance(request, number):
    """Quick 'advance to next status' button — one step forward."""
    order = get_object_or_404(Order, order_number=number)

    if order.status == "pending":
        messages.error(request, f"⚠️ {order.order_number} — payment not confirmed yet.")
        return redirect("staff:order_detail", number=number)

    if not order.paid_at:
        messages.error(request, f"⚠️ {order.order_number} — no payment record.")
        return redirect("staff:order_detail", number=number)

    next_status = NEXT_STATUS.get(order.status)
    if not next_status:
        messages.info(request, f"{order.order_number} is at final stage or cancelled.")
        return redirect("staff:order_detail", number=number)

    old_status = order.status
    order.status = next_status
    if next_status == "shipped" and not order.shipped_at:
        order.shipped_at = timezone.now()
    elif next_status == "picked_up" and not order.delivered_at:
        order.delivered_at = timezone.now()
    order.save(update_fields=["status", "shipped_at", "delivered_at"])

    TrackingHistory.objects.update_or_create(
        order=order,
        status=next_status,
        defaults={"note": STATUS_NOTES.get(next_status, f"Status: {next_status}")},
    )

    messages.success(
        request,
        f"✅ {order.order_number}: {old_status} → {next_status}. Customer tracking updated.",
    )
    return redirect("staff:order_detail", number=number)


@staff_member_required(login_url="account_login")
@require_POST
def order_change_status(request, number):
    """Manually set order status via the dropdown (any valid transition)."""
    order = get_object_or_404(Order, order_number=number)
    new_status = request.POST.get("status", "").strip()
    receipt = request.POST.get("mpesa_receipt", "").strip()

    # 1. Validate the target status exists
    valid_keys = [k for k, _ in ORDER_STATUS_CHOICES]
    if new_status not in valid_keys:
        messages.error(request, f"Invalid status: {new_status}")
        return redirect("staff:order_detail", number=number)

    # 2. No-op if unchanged
    if new_status == order.status:
        messages.info(request, f"{order.order_number} is already '{new_status}'.")
        return redirect("staff:order_detail", number=number)

    # 3. Enforce the allowed transition map
    allowed = VALID_STATUS_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        messages.error(
            request,
            f"Cannot change from '{order.status}' to '{new_status}'. "
            f"Allowed: {', '.join(allowed) if allowed else 'none (terminal state)'}",
        )
        return redirect("staff:order_detail", number=number)

    old_status = order.status
    order.status = new_status

    # 4. Update timestamps as needed
    if new_status == "paid" and not order.paid_at:
        order.paid_at = timezone.now()
    elif new_status == "shipped" and not order.shipped_at:
        order.shipped_at = timezone.now()
    elif new_status == "picked_up" and not order.delivered_at:
        order.delivered_at = timezone.now()
        # 4. Update timestamps as needed
    if new_status == "paid" and not order.paid_at:
        order.paid_at = timezone.now()
    elif new_status == "shipped" and not order.shipped_at:
        order.shipped_at = timezone.now()
    elif new_status == "picked_up" and not order.delivered_at:
        order.delivered_at = timezone.now()
    elif new_status == "cancelled" and not order.cancelled_at:
        order.cancelled_at = timezone.now()

    # 5. Optional receipt when manually marking as paid
        update_fields = ["status", "paid_at", "shipped_at", "delivered_at", "cancelled_at"]    if new_status == "paid" and receipt:
        order.mpesa_receipt = receipt
        update_fields.append("mpesa_receipt")

    order.save(update_fields=update_fields)

    # 6. Log a tracking history entry
    note = f"[Manual: {old_status} → {new_status}] {STATUS_NOTES.get(new_status, '')}".strip()
    TrackingHistory.objects.create(
        order=order,
        status=new_status,
        note=note,
    )

    messages.success(
        request,
        f"✅ {order.order_number}: {old_status} → {new_status}.",
    )
    return redirect("staff:order_detail", number=number)


# ============================================================
# CUSTOMERS
# ============================================================

from django.contrib.auth.models import User

PAID_STATUSES = ["paid", "processing", "shipped", "ready_for_pickup", "picked_up"]


@staff_member_required(login_url="account_login")
def customers_list(request):
    filter_type = request.GET.get("filter", "all")
    q = request.GET.get("q", "").strip()

    users = (
        User.objects.filter(is_staff=False)
        .annotate(
            order_count=Count("orders", distinct=True),
            total_spent=Sum("orders__total", filter=Q(orders__status__in=PAID_STATUSES)),
            last_order=Max("orders__created_at"),
        )
        .order_by("-last_order", "-date_joined")
    )

    if filter_type == "with_orders":
        users = users.filter(order_count__gt=0)
    elif filter_type == "no_orders":
        users = users.filter(order_count=0)

    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )

    paginator = Paginator(users, 30)
    users_page = paginator.get_page(request.GET.get("page", 1))

    base_users = User.objects.filter(is_staff=False)
    total_count = base_users.count()
    with_orders_count = base_users.filter(orders__isnull=False).distinct().count()
    no_orders_count = total_count - with_orders_count

    return render(request, "staff/customers.html", {
        "users": users_page,
        "paginator": paginator,
        "filter_type": filter_type,
        "q": q,
        "total_count": total_count,
        "with_orders_count": with_orders_count,
        "no_orders_count": no_orders_count,
    })


@staff_member_required(login_url="account_login")
def customer_detail(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False)

    orders = customer.orders.select_related("user").prefetch_related("items").order_by("-created_at")

    total_spent = (
        orders.filter(status__in=PAID_STATUSES).aggregate(t=Sum("total"))["t"] or 0
    )
    paid_count = orders.filter(status__in=PAID_STATUSES).count()

    return render(request, "staff/customer_detail.html", {
        "customer": customer,
        "orders": orders[:50],
        "total_orders": orders.count(),
        "paid_count": paid_count,
        "total_spent": total_spent,
    })