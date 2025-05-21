from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="products:home"),
        name="logout",
    ),
    path("profile/", views.profile, name="profile"),
    path("address/add/", views.AddressCreateView.as_view(), name="add_address"),
    path(
        "address/<int:pk>/update/",
        views.AddressUpdateView.as_view(),
        name="update_address",
    ),
    path("address/<int:pk>/delete/", views.delete_address, name="delete_address"),
    path(
        "seller/profile/",
        views.SellerProfileUpdateView.as_view(),
        name="seller_profile",
    ),
    path('shop/<int:pk>/', views.ShopProfileView.as_view(), name='shop_profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
