# chat/urls.py
from django.urls import path
from . import views # Sẽ tạo view này

app_name = 'chat'

urlpatterns = [
    # URL này sẽ dùng để seller vào một phòng chat cụ thể
    path('seller/room/<int:room_id>/', views.seller_chat_room_view, name='seller_chat_room'),
    # Bạn có thể thêm một trang liệt kê tất cả các phòng chat của seller ở đây nếu muốn
    path('seller/list/', views.seller_chat_list_view, name='seller_chat_list'),
]