from .cart import Cart
from .models import Wishlist

def cart_summary(request):
    cart = Cart(request)
    return {
        "cart_count": len(cart),
        "cart_total": cart.total,
    }
def cart_summary(request):
    cart = Cart(request)
    
    # Get wishlist data if user is logged in
    wishlist_count = 0
    wishlist_product_ids = []
    
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
        wishlist_count = wishlist_items.count()
        wishlist_product_ids = list(wishlist_items.values_list('product_id', flat=True))

    return {
        "cart_count": len(cart),
        "cart_total": cart.total,
        "wishlist_count": wishlist_count,
        "wishlist_product_ids": wishlist_product_ids,
    }