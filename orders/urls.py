from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/<int:pk>/", views.order_success, name="order_success"),
    path("list/", views.OrderListView.as_view(), name="order_list"),
    path("detail/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("seller/orders/", views.seller_orders, name="seller_orders"),
    path(
        "seller/orders/<int:order_id>/",
        views.seller_order_detail,
        name="seller_order_detail",
    ),
    path(
        "seller/orders/<int:order_id>/update-status/",
        views.update_order_status,
        name="update_order_status",
    ),
    path("order/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),
    path("payos/return/", views.payos_return_view, name="payos_return"),
    path("payos/cancel/", views.payos_cancel_view, name="payos_cancel"),
    path("payos/webhook/", views.payos_webhook_view, name="payos_webhook"),
]
