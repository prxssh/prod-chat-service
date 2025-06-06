from __future__ import annotations

import json
import uuid
import logging
from urllib.parse import parse_qs
from typing import Dict, Set, Optional, Any
from channels.generic.websocket import AsyncWebsocketConsumer
from app.metrics import total_messages, active_connections, error_count
from websockets.exceptions import ConnectionClosedOK
from uvicorn.protocols.utils import ClientDisconnected

logger = logging.getLogger(__name__)

# in-memory session store that maps (session_id -> count)
SESSIONS: Dict[str, int] = {}
ACTIVE_CONNECTIONS: Set[ChatConsumer]= set()

class ChatConsumer(AsyncWebsocketConsumer):
    group_name: str = "broadcast"
    session_id: str
    count: int

    async def connect(self):
        """
        Handles the WebSocket connection handshake.
        - Accepts connection.
        - Resumes session if session ID is provided and in memory.
        - Increments active connection count.
        - Logs connection event.
        """
        try:
            qs: Dict[str, list[str]] = parse_qs(self.scope["query_string"].decode())
            raw: Optional[str] = qs.get("session", [None])[0]

            if raw and raw in SESSIONS:
                self.session_id = raw
                self.count = SESSIONS[raw]
            else:
                self.session_id = str(uuid.uuid4())
                self.count = 0
                SESSIONS[self.session_id] = self.count 

            logger.info("WebSocket connected", extra={
                "session_id": self.session_id,
                "count": self.count
            })

            await self.accept()
            await self.channel_layer.group_add(self.group_name, self.channel_name)

            active_connections.inc()
            ACTIVE_CONNECTIONS.add(self)

            await self.send(text_data=self.build_normal_response())

        except (ConnectionClosedOK, ClientDisconnected):
            return

        except Exception as e:
            logger.exception("Connection failed", extra={
                "error": str(e)
            })
            await self.close(code=1011)

    async def receive(self, text_data: Optional[str] = None, bytes_data: Optional[str] = None) ->  None:
        """
        Handles incoming WebSocket messages.
        - If message is 'close', closes the socket cleanly.
        - Otherwise, increments message count and echoes response.
        - Increments `total_messages` metric.
        - Logs each received message.
        - Increments `error_count` on failure.
        """
        try:
            logger.info("Message received", extra={
                        "received_message": text_data,
                        "count": self.count,
                        "session_id": self.session_id
                    })

            total_messages.inc()

            if text_data == "close":
                await self.send(text_data=self.build_close_response())
                await self.close(code=1000)
            else:
                self.count += 1
                SESSIONS[self.session_id] = self.count

                await self.send(text_data=self.build_normal_response())

        except (ConnectionClosedOK, ClientDisconnected):
            return

        except Exception as e:
            logger.exception("Error while handling message", extra={
                "received_message": text_data,
                "session_id": self.session_id,
                "error": str(e)
            })

            error_count.inc()
            await self.close(code=1011)

    async def disconnect(self, code: int) -> None:
        """
        Called when the WebSocket disconnects (client or server side).
        - Logs disconnection reason and session data.
        - Sends final goodbye message.
        - Removes connection from active set.
        - Leaves broadcast group.
        - Decrements `active_connections` gauge.
        """
        logger.info("WebSocket disconnected", extra={
                    "code": code,
                    "count": self.count,
                    "session_id": self.session_id,
                })

        active_connections.dec()
        ACTIVE_CONNECTIONS.discard(self)

        try:
            await self.send(text_data=self.build_close_response())
        except Exception:
            pass

        # _SESSIONS.pop(self.session_id, None)
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception as e:
            logger.warning("Group discard failed", extra={
                "session_id": getattr(self, 'session_id', None),
                "error": str(e)
            })

            error_count.inc()

    async def heartbeat(self, event: Dict[str, Any]) -> None:
        """
        Sends a heartbeat ping to the client.
        Triggered by an external event via channel layer every 30s.
        """
        await self.send(text_data=json.dumps({"ts": event["ts"]}))

    async def close_socket(self) -> None:
        """
        Called on graceful shutdown (e.g. SIGTERM).
        - Sends final message.
        - Logs shutdown failure if it occurs.
        - Closes WebSocket with code 1001 ("going away").
        """
        try:
            await self.send(text_data=self.build_close_response())
        except Exception as e:
            logger.warning("Failed to send close message before shutdown", extra={
                "session_id": self.session_id,
                "error": str(e)
            })

            error_count.inc()

        await self.close(code=1001)

    def build_normal_response(self) -> str:
        return json.dumps({"session_id": self.session_id, "count": self.count})

    def build_close_response(self) -> str:
        return json.dumps({"session_id": self.session_id, "bye": True, "total": self.count})
