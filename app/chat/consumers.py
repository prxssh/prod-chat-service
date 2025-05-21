import json
import uuid
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer

# in-memory session store that maps (session_id -> count)
_SESSIONS = {}

class ChatConsumer(AsyncWebsocketConsumer):
    group_name = "broadcast"

    async def connect(self):
        qs = parse_qs(self.scope["query_string"].decode())
        raw = qs.get("session", [None])[0]
        print(raw, _SESSIONS)

        if raw and raw in _SESSIONS:
            self.session_id = raw
            self.count = _SESSIONS[raw]
        else:
            self.session_id = str(uuid.uuid4())
            self.count = 0
            _SESSIONS[self.session_id] = self.count 

        await self.accept()
        await self.send(text_data=self.build_normal_response())

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from client."""
        if text_data == "close":
            await self.send(text_data=self.build_close_response())
            await self.close(code=1000)
        else:
            self.count += 1
            _SESSIONS[self.session_id] = self.count

            await self.send(text_data=self.build_normal_response())

    async def disconnect(self, close_code):
        """Cleanup on disconnect. Send final message and leave group."""
        try:
            await self.send(text_data=self.build_close_response())
        except Exception:
            pass

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def heartbeat(self, event):
        """Receive heartbeat event from channel layer and forward to WebSocket."""
        await self.send(text_data=json.dumps({"ts": event["ts"]}))

    def build_normal_response(self):
        return json.dumps({"session_id": self.session_id, "count": self.count})

    def build_close_response(self):
        return json.dumps({"session_id": self.session_id, "bye": True, "total": self.count})
