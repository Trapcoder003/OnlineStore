from django.urls import path
from . import staff_views

app_name = "staff"

urlpatterns = [
    path("", staff_views.dashboard, name="dashboard"),

    # Products
    path("products/", staff_views.products_list, name="products"),
    path("products/new/", staff_views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", staff_views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", staff_views.product_delete, name="product_delete"),
    path("products/<int:pk>/stock/", staff_views.product_stock_update, name="product_stock_update"),

    # Orders
    path("orders/", staff_views.orders_list, name="orders"),
    path("orders/<str:number>/", staff_views.order_detail, name="order_detail"),
    path("orders/<str:number>/advance/", staff_views.order_advance, name="order_advance"),
    path("orders/<str:number>/change-status/", staff_views.order_change_status, name="order_change_status"),

    # Customers
    path("customers/", staff_views.customers_list, name="customers"),
    path("customers/<int:pk>/", staff_views.customer_detail, name="customer_detail"),
]