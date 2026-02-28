"""
SSE route — clients connect here to receive real-time XP update events.
"""

import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse import sse_manager, SSEClient

router = APIRouter(prefix='/api', tags=['sse'])


async def event_stream(client: SSEClient):
    """Generator that yields SSE-formatted events from the client's buffer."""
    try:
        while True:
            # Check for messages
            messages = client.get_all()
            if messages:
                for msg in messages:
                    yield f"data: {msg}\n\n"
            else:
                # No messages — send keepalive every 15 seconds
                # Poll more frequently so events are picked up quickly
                for _ in range(30):  # 30 * 0.5s = 15s
                    await asyncio.sleep(0.5)
                    messages = client.get_all()
                    if messages:
                        for msg in messages:
                            yield f"data: {msg}\n\n"
                        break
                else:
                    # No messages in 15s, send keepalive
                    yield ": keepalive\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        sse_manager.disconnect(client)


@router.get('/events')
async def sse_endpoint():
    """SSE endpoint — streams real-time XP update events to the client."""
    client = sse_manager.connect()
    return StreamingResponse(
        event_stream(client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
