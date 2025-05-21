from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # URL sẽ là /ws/chat/<product_id>/<seller_id>/
    # product_id: ID của sản phẩm đang xem
    # seller_id: ID của người bán sản phẩm đó
    re_path(r'ws/chat/product/(?P<product_id>\d+)/seller/(?P<seller_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]