"""
ASGI config for nusa_lapor_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# This code is default at django-nextjs: https://github.com/QueraTeam/django-nextjs

import os

from django.core.asgi import get_asgi_application
from django.urls import re_path, path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nusa_lapor_backend.settings")
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django_nextjs.proxy import NextJSProxyHttpConsumer, NextJSProxyWebsocketConsumer

from django.conf import settings

# put your custom routes here if you need
http_routes = [re_path(r"", django_asgi_app)]
websocket_routers = []

if settings.DEBUG:
    http_routes.insert(0, re_path(r"^(?:_next|__next|next).*", NextJSProxyHttpConsumer.as_asgi()))
    websocket_routers.insert(0, path("_next/webpack-hmr", NextJSProxyWebsocketConsumer.as_asgi()))


application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP and websocket requests.
        "http": URLRouter(http_routes),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_routers)),
        # ...
    }
)