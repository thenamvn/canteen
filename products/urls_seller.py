from django.urls import path
from . import views

app_name = 'seller'

urlpatterns = [
    path('dashboard/', views.seller_dashboard, name='dashboard'),
    path('product/add/', views.SellerProductCreateView.as_view(), name='add_product'),
    path('product/<int:pk>/update/', views.SellerProductUpdateView.as_view(), name='update_product'),
    path('product/<int:pk>/toggle/', views.toggle_product_availability, name='toggle_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
]