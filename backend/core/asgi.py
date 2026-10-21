"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django_asgi_app = get_asgi_application()

from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import OriginValidator
import chat.routing
import monitoring.routing

class SafeAllowedHostsOriginValidator(OriginValidator):
    """
    Validates WebSocket Origin header against settings.ALLOWED_HOSTS.
    Protects against Cross-Site WebSocket Hijacking (CSWSH) while permitting
    test communicators and non-browser clients without an Origin header.
    """
    def __init__(self, application):
        allowed_hosts = list(settings.ALLOWED_HOSTS)
        if settings.DEBUG and not allowed_hosts:
            allowed_hosts = ["localhost", "127.0.0.1", "[::1]"]
        if "testserver" not in allowed_hosts:
            allowed_hosts.append("testserver")
        super().__init__(application, allowed_hosts)

    def valid_origin(self, parsed_origin):
        if parsed_origin is None:
            return True
        return super().valid_origin(parsed_origin)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": SafeAllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                chat.routing.websocket_urlpatterns + monitoring.routing.websocket_urlpatterns
            )
        )
    ),
})

