"""
Session-based shopping cart.
Stores items as {product_id: {"qty": int, "price": str, "name": str, "slug": str}}
in request.session["cart"]. Swap for DB Order/OrderItem later.
"""
from decimal import Decimal
from django.conf import settings


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get("cart")
        if not cart:
            cart = self.session["cart"] = {}
        self.cart = cart
        self.coupon = self.session.get("coupon")  # {"code": str, "percent": int}

    # ---------- write ops ----------
    def add(self, product, qty=1, override=False):
        pid = str(product.id)
        if pid not in self.cart:
            self.cart[pid] = {
                "qty": 0,
                "price": str(product.price),
                "name": product.name,
                "slug": product.slug,
            }
        if override:
            self.cart[pid]["qty"] = qty
        else:
            self.cart[pid]["qty"] += qty

        if self.cart[pid]["qty"] > product.stock:
            self.cart[pid]["qty"] = product.stock
        if self.cart[pid]["qty"] < 1:
            self.cart[pid]["qty"] = 1

        self.save()

    def update(self, product_id, qty):
        pid = str(product_id)
        if pid in self.cart:
            self.cart[pid]["qty"] = max(1, int(qty))
            self.save()

    def remove(self, product_id):
        pid = str(product_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        self.session["cart"] = {}
        self.session.pop("coupon", None)
        self.cart = {}
        self.coupon = None
        self.save()

    def save(self):
        self.session.modified = True

    # ---------- coupon ----------
    def apply_coupon(self, code):
        code = (code or "").strip().upper()
        if not code:
            return False, "Enter a code."
        valid = getattr(settings, "COUPONS", {})
        if code not in valid:
            return False, "That code isn't valid."
        self.session["coupon"] = {"code": code, "percent": valid[code]}
        self.coupon = self.session["coupon"]
        self.save()
        return True, f"{code} applied — {valid[code]}% off."

    def remove_coupon(self):
        self.session.pop("coupon", None)
        self.coupon = None
        self.save()

    # ---------- read ----------
    def __len__(self):
        return sum(i["qty"] for i in self.cart.values())

    def __iter__(self):
        from .models import Product
        ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=ids)
        for p in products:
            item = self.cart[str(p.id)]
            item["product"] = p
            item["subtotal"] = Decimal(item["price"]) * item["qty"]
            yield item

    @property
    def subtotal(self):
        return sum((Decimal(i["price"]) * i["qty"]) for i in self.cart.values()) or Decimal("0.00")

    @property
    def discount(self):
        if not self.coupon:
            return Decimal("0.00")
        return (self.subtotal * Decimal(self.coupon["percent"]) / 100).quantize(Decimal("0.01"))

    @property
    def shipping(self):
        after = self.subtotal - self.discount
        if after <= 0:
            return Decimal("0.00")
        if after >= 5000:
            return Decimal("0.00")
        return Decimal("300.00")

    @property
    def total(self):
        return (self.subtotal - self.discount + self.shipping).quantize(Decimal("0.01"))

    @property
    def free_shipping_gap(self):
        after = self.subtotal - self.discount
        if after >= 5000 or after <= 0:
            return Decimal("0.00")
        return (Decimal("5000") - after).quantize(Decimal("0.01"))