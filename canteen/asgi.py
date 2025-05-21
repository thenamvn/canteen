"""
ASGI config for canteen project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen.settings')

application = get_asgi_application()

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app, # Định tuyến HTTP requests đến Django views thông thường
    "websocket": AuthMiddlewareStack( # AuthMiddlewareStack để truy cập request.user trong consumer
        URLRouter(
            chat.routing.websocket_urlpatterns # Định tuyến WebSocket đến chat consumers
        )
    ),
})