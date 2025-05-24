"""
ASGI config for app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import asyncio
import threading, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

from concurrent.futures import ThreadPoolExecutor
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from app.chat.routing import websocket_urlpatterns
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from datetime import datetime, timezone
from app.shutdown import register_shutdown


loop = asyncio.get_event_loop()
max_workers = int(os.getenv("THREADPOOL_MAX_WORKERS", "50"))
loop.set_default_executor(ThreadPoolExecutor(max_workers=max_workers))

register_shutdown()

def start_heartbeat():
    layer = get_channel_layer()
    if layer is None:
        raise RuntimeError("No channel layer configured")

    def tick():
        while True:
            ts = datetime.now(timezone.utc).isoformat()
            async_to_sync(layer.group_send)(
                "broadcast",
                {"type": "heartbeat", "ts": ts}
            )
            time.sleep(30)
    thread = threading.Thread(target=tick, daemon=True)
    thread.start()

start_heartbeat()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})
