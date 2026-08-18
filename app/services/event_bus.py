"""Asynchronous Event Bus for real-time task event streaming."""

import asyncio
import logging
from typing import AsyncGenerator, Dict, Set
from app.models.task import TaskEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Pub/Sub Event Bus for broadcasting task events to SSE/WebSocket subscribers."""

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

    def subscribe(self, task_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific task."""
        if task_id not in self._subscribers:
            self._subscribers[task_id] = set()
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[task_id].add(queue)
        logger.debug(f"Subscriber added for task {task_id}. Total: {len(self._subscribers[task_id])}")
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from a task event stream."""
        if task_id in self._subscribers:
            self._subscribers[task_id].discard(queue)
            if not self._subscribers[task_id]:
                del self._subscribers[task_id]
        logger.debug(f"Subscriber removed for task {task_id}")

    async def publish(self, task_id: str, event: TaskEvent) -> None:
        """Broadcast an event to all active task subscribers."""
        if task_id in self._subscribers:
            for queue in list(self._subscribers[task_id]):
                await queue.put(event)

    async def event_generator(self, task_id: str) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE formatted strings for FastAPI streaming."""
        queue = self.subscribe(task_id)
        try:
            while True:
                event: TaskEvent = await queue.get()
                yield f"event: {event.event_type}\ndata: {event.model_dump_json()}\n\n"
        finally:
            self.unsubscribe(task_id, queue)


# Global Singleton Event Bus
global_event_bus = EventBus()
