# chat/urls.py
from django.urls import path
from . import views # Sẽ tạo view này

app_name = 'chat'

urlpatterns = [
    # URL này sẽ dùng để seller vào một phòng chat cụ thể
    path('seller/room/<int:room_id>/', views.seller_chat_room_view, name='seller_chat_room'),
    path('seller/list/', views.seller_chat_list_view, name='seller_chat_list'),
]