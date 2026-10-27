from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("category/<slug:slug>/", views.category_detail, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product"),
    path("search/", views.search, name="search"),

    # Cart
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("cart/coupon/apply/", views.cart_apply_coupon, name="cart_apply_coupon"),
    path("cart/coupon/remove/", views.cart_remove_coupon, name="cart_remove_coupon"),

    # Info pages
    path("contact/", views.contact, name="contact"),
    path("contact/success/", views.contact_success, name="contact_success"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("shipping-returns/", views.shipping_returns, name="shipping"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("mpesa/pay/", views.mpesa_pay, name="mpesa_pay"),
    path("mpesa/callback/", views.mpesa_callback, name="mpesa_callback"),
    path("wishlist/", views.wishlist_detail, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("product/<slug:slug>/review/", views.add_review, name="add_review"),
    path("review/<int:review_id>/delete/", views.delete_review, name="delete_review"),
        # Orders
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<str:number>/", views.order_detail, name="order_detail"),
    path("orders/<str:number>/waiting/", views.order_waiting, name="order_waiting"),
    path("orders/<str:number>/status/", views.order_status_json, name="order_status"),
    path("account/orders/", views.order_history, name="order_history"),
]