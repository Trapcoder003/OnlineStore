from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction
from django.db.models import Q, Avg, Sum
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
import json


from allauth.account.views import PasswordResetFromKeyView as AllauthPasswordResetFromKeyView
from allauth.account.forms import UserTokenForm

from .models import (
    Wishlist, Product, Category, Review,
    Order, OrderItem, TrackingHistory, UserProfile,
)
from .cart import Cart
from .forms import ContactForm, CheckoutForm, AvatarUploadForm

# ---------------- MAIN PAGES ----------------

def home(request):
    featured = Product.objects.filter(is_featured=True, stock__gt=0).order_by("-sold_count", "name")[:8]
    new_arrivals = Product.objects.filter(stock__gt=0).order_by("-id")[:8]
    best_sellers = Product.objects.filter(sold_count__gt=0, stock__gt=0).order_by("-sold_count")[:8]

    return render(request, "pages/home.html", {
        "categories": Category.objects.all()[:6],
        "featured": featured,
        "new_arrivals": new_arrivals,
        "best_sellers": best_sellers,
    })


def shop(request):
    return render(request, "pages/shop.html", {"products": Product.objects.all()})


def about(request):      return render(request, "pages/about.html")
def faq(request):        return render(request, "pages/faq.html")
def shipping_returns(request): return render(request, "pages/shipping.html")
def privacy(request):    return render(request, "pages/privacy.html")
def terms(request):      return render(request, "pages/terms.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        send_mail(f"Message from {d['name']}", d["message"], d["email"], ["you@yourshop.com"])
        return redirect("contact_success")
    return render(request, "pages/contact.html", {"form": form})


def contact_success(request):
    return render(request, "pages/success.html")


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()
    sort = request.GET.get("sort", "")
    if sort == "low":  products = products.order_by("price")
    elif sort == "high": products = products.order_by("-price")
    elif sort == "az": products = products.order_by("name")
    return render(request, "pages/category.html", {
        "category": category, "products": products,
        "siblings": Category.objects.exclude(pk=category.pk), "sort": sort,
    })


def search(request):
    q = request.GET.get("q", "").strip()
    cat_slug = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "").strip()
    availability = request.GET.get("availability", "all")
    products = Product.objects.all()

    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q) |
            Q(brand__icontains=q) | Q(category__name__icontains=q)
        )
    if cat_slug:
        products = products.filter(category__slug=cat_slug)
    if availability == "in":
        products = products.filter(stock__gt=0)
    elif availability == "low":
        products = products.filter(stock__lt=5, stock__gt=0)

    if sort == "low":   products = products.order_by("price")
    elif sort == "high": products = products.order_by("-price")
    elif sort == "az":  products = products.order_by("name")
    elif sort == "new": products = products.order_by("-id")
    else:               products = products.order_by("-is_featured", "name")

    return render(request, "pages/search.html", {
        "q": q, "products": products,
        "categories": Category.objects.all(),
        "selected_category": cat_slug, "sort": sort, "availability": availability,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related = (Product.objects
               .filter(category=product.category)
               .exclude(pk=product.pk)
               .order_by("-is_featured", "name")[:4])
    reviews = (
    product.reviews
    .select_related("user", "user__profile")
    .order_by("-created_at")
)
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    return render(request, "pages/product.html", {
        "product": product, "related": related, "reviews": reviews,
        "rating_avg": round(avg_rating, 1), "rating_count": reviews.count(),
        "user_review": user_review,
    })

# ---------------- USER PROFILE ----------------

@login_required
def profile_settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = AvatarUploadForm(
            request.POST, request.FILES, instance=profile
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile_settings")
    else:
        form = AvatarUploadForm(instance=profile)

    return render(request, "account/profile_settings.html", {
        "form": form,
        "profile": profile,
    })


# ---------------- CART ----------------

def cart_detail(request):
    cart = Cart(request)
    return render(request, "pages/cart.html", {"cart": cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    qty = int(request.POST.get("qty", 1))

    if product.stock < 1:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect(request.POST.get("next") or "cart")

    cart.add(product, qty=qty)
    messages.success(request, f"{product.name} added to cart.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "cart_count": len(cart), "cart_total": f"{cart.total:.2f}"})
    return redirect(request.POST.get("next") or "cart")


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    qty = int(request.POST.get("qty", 1))
    cart.update(product_id, qty)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True, "cart_count": len(cart),
            "subtotal": f"{cart.subtotal:.2f}", "discount": f"{cart.discount:.2f}",
            "shipping": f"{cart.shipping:.2f}", "total": f"{cart.total:.2f}",
        })
    return redirect("cart")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True, "cart_count": len(cart),
            "subtotal": f"{cart.subtotal:.2f}", "discount": f"{cart.discount:.2f}",
            "shipping": f"{cart.shipping:.2f}", "total": f"{cart.total:.2f}",
        })
    return redirect("cart")


@require_POST
def cart_apply_coupon(request):
    cart = Cart(request)
    ok, msg = cart.apply_coupon(request.POST.get("code"))
    (messages.success if ok else messages.error)(request, msg)
    return redirect("cart")


@require_POST
def cart_remove_coupon(request):
    cart = Cart(request)
    cart.remove_coupon()
    messages.info(request, "Coupon removed.")
    return redirect("cart")


# ---------------- CHECKOUT ----------------

DELIVERY_FEES = {"pickup": 0, "standard": 300, "express": 500}
FREE_SHIPPING_THRESHOLD = 5000


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, "Your cart is empty. Add some products first.")
        return redirect("shop")

    initial = {
        "email": request.user.email if request.user.is_authenticated else "",
        "ship_name": request.user.get_full_name() if request.user.is_authenticated else "",
    }

    form = CheckoutForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data

        for item in cart:
            product = item["product"]
            qty = item["qty"]
            if product.stock < qty:
                messages.error(
                    request,
                    f"Only {product.stock} of {product.name} left. Please reduce quantity.",
                )
                return redirect("cart")

        subtotal = cart.subtotal
        discount = cart.discount
        delivery_fee = DELIVERY_FEES[d["delivery_method"]]
        if d["delivery_method"] != "pickup" and subtotal >= FREE_SHIPPING_THRESHOLD:
            delivery_fee = 0
        total = subtotal - discount + delivery_fee

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=d["email"],
                phone=d["phone"],
                ship_name=d["ship_name"],
                ship_phone=d["ship_phone"],
                ship_county=d["ship_county"],
                ship_town=d["ship_town"],
                ship_address=d["ship_address"],
                delivery_method=d["delivery_method"],
                notes=d.get("notes", ""),
                subtotal=subtotal,
                shipping_fee=delivery_fee,
                discount=discount,
                total=total,
            )

            for item in cart:
                product = item["product"]
                qty = item["qty"]
                unit_price = item["price"]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_slug=product.slug,
                    product_image_url=product.image.url if product.image else "",
                    unit_price=unit_price,
                    qty=qty,
                )

        try:
            response = initiate_stk_push(
                d["phone"],
                int(total),
                order.order_number,
                f"E-Shop {order.order_number}",
            )
            checkout_id = response.get("CheckoutRequestID", "")
            if checkout_id:
                order.mpesa_checkout_id = checkout_id
                order.save()
        except Exception as e:
            order.notes = f"{order.notes}\n\nSTK Push error: {e}"
            order.save()
            messages.error(request, "Payment could not be initiated. Please try again.")
            return redirect("order_waiting", number=order.order_number)

        return redirect("order_waiting", number=order.order_number)

    return render(request, "pages/checkout.html", {"form": form, "cart": cart})


def order_waiting(request, number):
    order = get_object_or_404(Order, order_number=number)
    return render(request, "pages/order_waiting.html", {"order": order})


def order_status_json(request, number):
    order = get_object_or_404(Order, order_number=number)
    track_url = f"/track/{order.order_number}/" if order.status == "paid" else ""
    return JsonResponse({
        "status": order.status,
        "receipt": order.mpesa_receipt,
        "url": track_url,
    })


def order_detail(request, number):
    order = get_object_or_404(Order, order_number=number)
    if (
        order.user
        and request.user.is_authenticated
        and order.user != request.user
        and not request.user.is_staff
    ):
        messages.error(request, "You don't have access to this order.")
        return redirect("home")
    return render(request, "pages/order_detail.html", {"order": order})


def order_receipt(request, number):
    """Printable receipt page — customer can Ctrl+P → Save as PDF."""
    order = get_object_or_404(Order, order_number=number)

    if (
        order.user
        and request.user.is_authenticated
        and order.user != request.user
        and not request.user.is_staff
    ):
        messages.error(request, "You don't have access to this receipt.")
        return redirect("home")

    return render(request, "pages/order_receipt.html", {"order": order})


def order_history(request):
    if not request.user.is_authenticated:
        return redirect("account_login")
    orders = (
    Order.objects
    .filter(user=request.user)
    .select_related("user", "user__profile")
    .prefetch_related("items")
)
    return render(request, "pages/order_history.html", {"orders": orders})


# ---------------- ORDER TRACKING ----------------

def track_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    history = order.tracking_history.all()
    history_by_status = {h.status: h for h in history}

    pipeline = [
        ("paid",             "Payment confirmed",          "💳"),
        ("processing",       "Processing your order",      "⚙️"),
        ("shipped",          "Shipped to pickup station",  "🚚"),
        ("ready_for_pickup", "Ready for pickup",           "📦"),
        ("picked_up",        "Picked up",                  "✅"),
    ]

    steps = []
    for key, label, icon in pipeline:
        entry = history_by_status.get(key)
        steps.append({
            "key": key,
            "label": label,
            "icon": icon,
            "done": entry is not None,
            "at": entry.created_at if entry else None,
            "note": entry.note if entry else "",
        })

    return render(request, "pages/track_order.html", {
        "order": order,
        "history": history,
        "steps": steps,
    })


# ---------------- OWNER DASHBOARD ----------------

ADVANCEABLE_STATUSES = {"paid", "processing", "shipped", "ready_for_pickup"}

NEXT_STATUS = {
    "paid":             "processing",
    "processing":       "shipped",
    "shipped":          "ready_for_pickup",
    "ready_for_pickup": "picked_up",
}


@staff_member_required
def staff_orders_dashboard(request):
    status_filter = request.GET.get("status", "active")
    q = request.GET.get("q", "").strip()

    orders = Order.objects.all()

    if status_filter == "active":
        orders = orders.exclude(status__in=["picked_up", "cancelled", "failed"])
    elif status_filter == "all":
        pass
    else:
        orders = orders.filter(status=status_filter)

    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(phone__icontains=q) |
            Q(email__icontains=q) |
            Q(ship_name__icontains=q)
        )

    orders = (
    orders
    .select_related("user", "user__profile")
    .prefetch_related("items")
    .order_by("-created_at")
)

    paginator = Paginator(orders, 30)
    page = request.GET.get("page", 1)
    orders_page = paginator.get_page(page)

    today = timezone.now().date()
    stats = {
        "pending":          Order.objects.filter(status="pending").count(),
        "paid":             Order.objects.filter(status="paid").count(),
        "processing":       Order.objects.filter(status="processing").count(),
        "shipped":          Order.objects.filter(status="shipped").count(),
        "ready_for_pickup": Order.objects.filter(status="ready_for_pickup").count(),
        "picked_up_today":  Order.objects.filter(
                                status="picked_up",
                                delivered_at__date=today,
                            ).count(),
        "today_revenue":    Order.objects.filter(
                                status__in=[
                                    "paid", "processing", "shipped",
                                    "ready_for_pickup", "picked_up",
                                ],
                                paid_at__date=today,
                            ).aggregate(total=Sum("total"))["total"] or 0,
    }

    return render(request, "staff/orders_dashboard.html", {
        "orders": orders_page,
        "status_filter": status_filter,
        "q": q,
        "stats": stats,
        "paginator": paginator,
    })


@staff_member_required
@require_POST
def staff_advance_order(request, order_number):
    """
    One-click advance to the next status.
    BLOCKS advancement if payment hasn't been confirmed.
    """
    order = get_object_or_404(Order, order_number=order_number)
    referer = request.META.get("HTTP_REFERER", "staff_orders_dashboard")

    if order.status == "pending":
        messages.error(
            request,
            f"⚠️ {order.order_number} cannot advance — payment has not been confirmed yet.",
        )
        return redirect(referer)

    if order.status == "failed":
        messages.error(
            request,
            f"❌ {order.order_number} payment failed. Cannot advance a failed order.",
        )
        return redirect(referer)

    if order.status in ("picked_up", "cancelled"):
        messages.info(request, f"{order.order_number} is already complete.")
        return redirect(referer)

    if not order.paid_at:
        messages.error(
            request,
            f"⚠️ {order.order_number} has no confirmed payment record. Cannot advance.",
        )
        return redirect(referer)

    next_status = NEXT_STATUS.get(order.status)
    if not next_status:
        messages.info(request, f"{order.order_number} is already at the final stage.")
        return redirect(referer)

    old_status = order.status
    order.status = next_status

    if next_status == "shipped" and not order.shipped_at:
        order.shipped_at = timezone.now()
    elif next_status == "picked_up" and not order.delivered_at:
        order.delivered_at = timezone.now()

    order.save(update_fields=["status", "shipped_at", "delivered_at"])

    note_map = {
        "processing":       "Your order is confirmed and being prepared.",
        "shipped":          f"Dispatched to {order.pickup_station_name or 'your pickup station'}.",
        "ready_for_pickup": f"Ready for pickup! Bring your ID and order number {order.order_number}.",
        "picked_up":        "Collected. Thank you for shopping with us!",
    }

    TrackingHistory.objects.update_or_create(
        order=order,
        status=next_status,
        defaults={"note": note_map.get(next_status, f"Status updated to {next_status}.")},
    )

    messages.success(
        request,
        f"✅ {order.order_number}: {old_status} → {next_status}. Customer notified.",
    )
    return redirect(referer)


# ---------------- M-PESA INTEGRATION ----------------

@require_POST
def mpesa_pay(request):
    try:
        data = json.loads(request.body)
        response = initiate_stk_push(data.get("phone"), data.get("amount"), "LEGACY", "E-Shop Payment")
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def mpesa_callback(request):
    if request.method != "POST":
        return JsonResponse({"ResultCode": 0, "ResultDesc": "OK"})

    try:
        data = json.loads(request.body)
        stk = data["Body"]["stkCallback"]
        result_code = stk["ResultCode"]
        result_desc = stk.get("ResultDesc", "")
        checkout_id = stk.get("CheckoutRequestID", "")

        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(mpesa_checkout_id=checkout_id)
            except Order.DoesNotExist:
                print(f"⚠️  Callback for unknown CheckoutRequestID: {checkout_id}")
                return JsonResponse({"ResultCode": 0, "ResultDesc": "OK"})

            if order.status == "paid":
                print(f"ℹ️  Duplicate callback ignored: {order.order_number}")
                return JsonResponse({"ResultCode": 0, "ResultDesc": "OK"})

            if result_code == 0:
                metadata = stk.get("CallbackMetadata", {}).get("Item", [])
                receipt = next((i["Value"] for i in metadata if i["Name"] == "MpesaReceiptNumber"), "")
                phone = next((i["Value"] for i in metadata if i["Name"] == "PhoneNumber"), "")

                for item in order.items.all():
                    if item.product_id:
                        product = Product.objects.select_for_update().get(pk=item.product_id)
                        if product.stock >= item.qty:
                            product.stock -= item.qty
                            product.sold_count += item.qty
                            product.save()
                        else:
                            order.notes += f"\n⚠️ Oversold: {product.name} (had {product.stock}, needed {item.qty})"
                            product.stock = 0
                            product.sold_count += item.qty
                            product.save()

                order.mark_paid(receipt=str(receipt), phone=str(phone), description=result_desc)

                try:
                    TrackingHistory.objects.create(
                        order=order,
                        status="paid",
                        note=f"Payment confirmed. M-Pesa receipt: {receipt}",
                    )
                except Exception as e:
                    print(f"Tracking entry error for {order.order_number}: {e}")

                try:
                    cart = Cart(request)
                    cart.clear()
                except Exception as e:
                    print(f"Cart clear error: {e}")

                try:
                    send_order_confirmation_email(order)
                except Exception as e:
                    print(f"Email error for {order.order_number}: {e}")

                print(f"✅ PAID: {order.order_number} · Receipt {receipt} · KES {order.total}")

            else:
                order.status = "failed"
                order.mpesa_result_desc = result_desc
                order.save()
                print(f"❌ FAILED: {order.order_number} · {result_desc}")

    except Exception as e:
        print(f"Callback error: {e}")

    return JsonResponse({"ResultCode": 0, "ResultDesc": "OK"})


def send_order_confirmation_email(order):
    """Send receipt + order summary with working links."""
    base_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")

    subject = f"Order confirmed · {order.order_number} · E-Shop"
    context = {
        "order": order,
        "base_url": base_url,
        "track_url": f"{base_url}/track/{order.order_number}/",
        "detail_url": f"{base_url}/orders/{order.order_number}/",
        "receipt_url": f"{base_url}/orders/{order.order_number}/receipt/",
    }

    text_body = render_to_string("emails/order_confirmation.txt", context)
    html_body = render_to_string("emails/order_confirmation.html", context)

    from django.core.mail import EmailMultiAlternatives
    msg = EmailMultiAlternatives(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


# ---------------- CUSTOM PASSWORD RESET ----------------

class CustomPasswordResetFromKeyView(AllauthPasswordResetFromKeyView):
    def dispatch(self, request, uidb36, key, **kwargs):
        self.request = request
        self.key = key
        token_form = UserTokenForm(data={"uidb36": uidb36, "key": self.key})
        if token_form.is_valid():
            self.reset_user = token_form.reset_user
            return self.render_to_response(self.get_context_data())
        self.reset_user = None
        return self.render_to_response(self.get_context_data(token_fail=True))

    # ✅ NEW: expose reset_user so the template shows "Resetting password for <username>"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "reset_user" not in context:
            context["reset_user"] = getattr(self, "reset_user", None)
        return context


# ---------------- WISHLIST ----------------

def wishlist_detail(request):
    if not request.user.is_authenticated:
        return redirect("account_login")
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    return render(request, "pages/wishlist.html", {"items": items})


@require_POST
def toggle_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "login_required"}, status=401)
    product = get_object_or_404(Product, id=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        in_wishlist = False
    else:
        in_wishlist = True
    count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({"status": "success", "in_wishlist": in_wishlist, "count": count})


# ---------------- REVIEWS ----------------

@require_POST
def add_review(request, slug):
    if not request.user.is_authenticated:
        return redirect("account_login")
    product = get_object_or_404(Product, slug=slug)
    rating = request.POST.get("rating")
    comment = request.POST.get("comment")
    image = request.FILES.get("image")
    video = request.FILES.get("video")

    if rating and comment:
        review, created = Review.objects.get_or_create(
            product=product, user=request.user,
            defaults={"rating": rating, "comment": comment},
        )
        if not created:
            review.rating = rating
            review.comment = comment
        if image: review.image = image
        if video: review.video = video
        review.save()
        messages.success(request, "Your review has been saved!")
    else:
        messages.error(request, "Please provide a rating and a comment.")
    return redirect("product", slug=slug)


@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    slug = review.product.slug
    review.delete()
    messages.success(request, "Your review has been deleted.")
    return redirect("product", slug=slug)

