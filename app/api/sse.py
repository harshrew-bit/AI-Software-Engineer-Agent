"""Server-Sent Events streaming handler."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.event_bus import global_event_bus

sse_router = APIRouter()


@sse_router.get("/tasks/{task_id}/events")
async def stream_task_events(task_id: str):
    """Stream real-time task lifecycle and progress events using SSE."""
    return StreamingResponse(
        global_event_bus.event_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
