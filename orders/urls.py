from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:pk>/', views.order_success, name='order_success'),
    path('list/', views.OrderListView.as_view(), name='order_list'),
    path('detail/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]