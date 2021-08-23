import os
import django


from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from os2datascanner.projects.report.reportapp import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'os2datascanner.projects.report.settings')

django.setup()

from channels.auth import AuthMiddlewareStack

application = get_asgi_application()

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
    URLRouter(
      routing.websocket_urlpatterns
    )
  ),
})