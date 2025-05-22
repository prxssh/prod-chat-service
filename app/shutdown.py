import signal
import asyncio
import logging
from app.chat.consumers import ACTIVE_CONNECTIONS
from app import views as health_views
from app.metrics import shutdown_time

logger = logging.getLogger(__name__)
health_views.ready = True

def handle_sigterm(*_):
    logger.info("SIGTERM received", extra={"event": "shutdown_start"})

    health_views.ready = False
    loop = asyncio.get_event_loop()

    @shutdown_time.time()
    async def shutdown():
        await asyncio.gather(*(conn.close_socket() for conn in list(ACTIVE_CONNECTIONS)))
        logger.info("SIGTERM received", extra={"event": "shutdown_start"})

    loop.create_task(shutdown())

def register_shutdown():
    signal.signal(signal.SIGTERM, handle_sigterm)
