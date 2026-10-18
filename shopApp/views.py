from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .mpesa_service import initiate_stk_push
import json

from .models import Category, Product
from .cart import Cart
from .forms import ContactForm

def home(request):
    return render(request, "pages/home.html", {
        "categories": Category.objects.all()[:6],
        "featured": Product.objects.filter(is_featured=True)[:4],
    })

def shop(request):
    return render(request, "pages/shop.html", {"products": Product.objects.all()})

# Simple pages: each just shows its template
def about(request): 
    return render(request, "pages/about.html")
def faq(request): 
    return render(request, "pages/faq.html")
def shipping_returns(request): 
    return render(request, "pages/shipping.html")
def privacy(request): 
    return render(request, "pages/privacy.html")
def terms(request): 
    return render(request, "pages/terms.html")


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

    # Optional filters from the sidebar / sort dropdown (via GET)
    sort = request.GET.get("sort", "")
    if sort == "low":
        products = products.order_by("price")
    elif sort == "high":
        products = products.order_by("-price")
    elif sort == "az":
        products = products.order_by("name")

    return render(request, "pages/category.html", {
        "category": category,
        "products": products,
        "siblings": Category.objects.exclude(pk=category.pk),
        "sort": sort,
    })


def search(request):
    q = request.GET.get("q", "").strip()
    cat_slug = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "").strip()
    availability = request.GET.get("availability", "all")

    products = Product.objects.all()

    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(brand__icontains=q) |
            Q(category__name__icontains=q)
        )

    if cat_slug:
        products = products.filter(category__slug=cat_slug)

    if availability == "in":
        products = products.filter(stock__gt=0)
    elif availability == "low":
        products = products.filter(stock__lt=5, stock__gt=0)

    if sort == "low":
        products = products.order_by("price")
    elif sort == "high":
        products = products.order_by("-price")
    elif sort == "az":
        products = products.order_by("name")
    elif sort == "new":
        products = products.order_by("-id")
    else:
        products = products.order_by("-is_featured", "name")

    # Category list for the filter chips, with a count of matching products
    categories = Category.objects.all()

    return render(request, "pages/search.html", {
        "q": q,
        "products": products,
        "categories": categories,
        "selected_category": cat_slug,
        "sort": sort,
        "availability": availability,
    })

# CART

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
        return JsonResponse({
            "ok": True,
            "cart_count": len(cart),
            "cart_total": f"{cart.total:.2f}",
        })

    return redirect(request.POST.get("next") or "cart")


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    qty = int(request.POST.get("qty", 1))
    cart.update(product_id, qty)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "cart_count": len(cart),
            "subtotal": f"{cart.subtotal:.2f}",
            "discount": f"{cart.discount:.2f}",
            "shipping": f"{cart.shipping:.2f}",
            "total": f"{cart.total:.2f}",
        })

    return redirect("cart")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "cart_count": len(cart),
            "subtotal": f"{cart.subtotal:.2f}",
            "discount": f"{cart.discount:.2f}",
            "shipping": f"{cart.shipping:.2f}",
            "total": f"{cart.total:.2f}",
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

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # Related: same category, exclude self, cap at 4
    related = (Product.objects
               .filter(category=product.category)
               .exclude(pk=product.pk)
               .order_by("-is_featured", "name")[:4])

    # Fake rating stats for now — replace with a real Review model later
    rating_avg = 4.7
    rating_count = 128

    return render(request, "pages/product.html", {
        "product": product,
        "related": related,
        "rating_avg": rating_avg,
        "rating_count": rating_count,
    })



# ---------------- M-PESA INTEGRATION ----------------

@require_POST
def mpesa_pay(request):
    try:
        data = json.loads(request.body)
        phone = data.get("phone")
        amount = data.get("amount")
        
        # You can replace "ORDER123" with a real order ID later
        response = initiate_stk_push(phone, amount, "ORDER123", "E-Shop Payment")
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def mpesa_callback(request):
    """
    Safaricom sends the payment result to this URL.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Extract the result code (0 means success)
            result_code = data["Body"]["stkCallback"]["ResultCode"]
            
            if result_code == 0:
                # Payment successful! Extract receipt number
                metadata = data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
                receipt = next(item["Value"] for item in metadata if item["Name"] == "MpesaReceiptNumber")
                amount = next(item["Value"] for item in metadata if item["Name"] == "Amount")
                phone = next(item["Value"] for item in metadata if item["Name"] == "PhoneNumber")
                
                print(f"✅ PAYMENT SUCCESS: Receipt {receipt} | Phone: {phone} | Amount: {amount}")
                
                # TODO: Here you would mark the user's order as 'Paid' in your database.
                
            else:
                # Payment failed or was cancelled by the user
                print(f"❌ PAYMENT FAILED: ResultCode {result_code}")
                
        except Exception as e:
            print(f"Error processing callback: {e}")
            
    # Always return a success response to Safaricom so they don't retry
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})