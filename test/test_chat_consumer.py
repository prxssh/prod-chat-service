import json
import pytest
from channels.testing import WebsocketCommunicator

import app.chat.consumers as consumers


class DummyMetric:
    def __init__(self):
        self.value = 0
    def inc(self):
        self.value += 1
    def dec(self):
        self.value -= 1


@pytest.fixture(autouse=True)
def clear_state_and_patch(monkeypatch):
    # reset in-memory stores
    consumers.SESSIONS.clear()
    consumers.ACTIVE_CONNECTIONS.clear()
    # patch out real Prometheus metrics with our dummy
    monkeypatch.setattr(consumers, "total_messages", DummyMetric())
    monkeypatch.setattr(consumers, "active_connections", DummyMetric())
    monkeypatch.setattr(consumers, "error_count", DummyMetric())
    yield


@pytest.mark.asyncio
async def test_connect_generates_session_and_sends_initial_response():
    app = consumers.ChatConsumer.as_asgi()
    comm = WebsocketCommunicator(app, "/ws/chat/")
    connected, _ = await comm.connect()
    assert connected is True

    # On connect you get {"session_id": "...", "count": 0}
    msg = await comm.receive_from()
    payload = json.loads(msg)
    assert "session_id" in payload
    assert payload["count"] == 0

    # and we should have bumped active_connections once
    assert consumers.active_connections.value == 1

    # properly close
    await comm.disconnect()
    


@pytest.mark.asyncio
async def test_receive_increments_and_echoes():
    app = consumers.ChatConsumer.as_asgi()
    comm = WebsocketCommunicator(app, "/ws/chat/")
    assert (await comm.connect())[0]
    # swallow initial
    first = json.loads(await comm.receive_from())
    session = first["session_id"]

    # send a normal message
    await comm.send_to(text_data="hello")
    reply = json.loads(await comm.receive_from())
    assert reply["session_id"] == session
    assert reply["count"] == 1

    # metric was incremented
    assert consumers.total_messages.value == 1

    # properly close
    await comm.disconnect()
    


@pytest.mark.asyncio
async def test_close_message_closes_cleanly():
    app = consumers.ChatConsumer.as_asgi()
    comm = WebsocketCommunicator(app, "/ws/chat/")
    assert (await comm.connect())[0]
    # swallow initial
    _ = await comm.receive_from()

    # send the "close" command
    await comm.send_to(text_data="close")
    goodbye = json.loads(await comm.receive_from())
    assert goodbye["bye"] is True
    assert "total" in goodbye

    # after close, no further messages
    await comm.disconnect()
    


@pytest.mark.asyncio
async def test_reconnect_with_existing_session():
    app = consumers.ChatConsumer.as_asgi()
    # first connect to grab session ID
    c1 = WebsocketCommunicator(app, "/ws/chat/")
    assert (await c1.connect())[0]
    init = json.loads(await c1.receive_from())
    sid = init["session_id"]
    await c1.disconnect()

    # now connect again, passing session in query string
    c2 = WebsocketCommunicator(app, f"/ws/chat/?session={sid}")
    assert (await c2.connect())[0]
    resp = json.loads(await c2.receive_from())
    # should resume same session with count still = 0
    assert resp["session_id"] == sid
    assert resp["count"] == 0
    await c2.disconnect()
