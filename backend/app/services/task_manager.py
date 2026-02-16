"""Background Task Manager.

Manages a lightweight in-process async task queue with database-backed persistence.
Uses asyncio.create_task for non-blocking execution and SQLAlchemy for status tracking.

Architecture:
    - Tasks are created via `submit_task()`, which persists a pending record and
      immediately launches an asyncio coroutine.
    - Each coroutine wraps the caller-provided async function, updating status/progress
      in the DB as work proceeds.
    - Tasks can be cancelled via `cancel_task()`.
    - Automatic timeout cancellation is enforced via `asyncio.wait_for`.
    - A periodic cleanup removes old completed/failed tasks after a retention period.

Usage:
    from app.services.task_manager import task_manager

    async def my_long_operation(ctx):
        await ctx.update_progress(0.5, "Halfway done")
        result = await do_expensive_work()
        return {"url": result.url}

    task = await task_manager.submit_task(
        user_id=1,
        task_type="ai_image",
        title="KI-Bild generieren",
        func=my_long_operation,
        timeout_seconds=120,
    )
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Coroutine, Dict, List, Optional

import httpx
from sqlalchemy import select, update, delete, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.background_task import BackgroundTask

logger = logging.getLogger(__name__)

# Maximum number of tasks to retain per user for history
MAX_TASK_HISTORY = 50
# Retention period for completed/failed tasks (days)
TASK_RETENTION_DAYS = 7


class TaskContext:
    """Passed to task functions so they can report progress."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._cancelled = False

    async def update_progress(self, progress: float, status_text: Optional[str] = None):
        """Update task progress (0.0 - 1.0)."""
        if self._cancelled:
            raise asyncio.CancelledError("Task was cancelled")
        async with async_session() as session:
            values: Dict[str, Any] = {"progress": min(max(progress, 0.0), 1.0)}
            if status_text:
                values["result"] = json.dumps({"status_text": status_text})
            await session.execute(
                update(BackgroundTask)
                .where(BackgroundTask.task_id == self.task_id)
                .values(**values)
            )
            await session.commit()

    def check_cancelled(self):
        if self._cancelled:
            raise asyncio.CancelledError("Task was cancelled")


class TaskManager:
    """Singleton task manager for the application."""

    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def submit_task(
        self,
        user_id: int,
        task_type: str,
        title: str,
        func: Callable[[TaskContext], Coroutine[Any, Any, Any]],
        timeout_seconds: int = 300,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a new background task.

        Args:
            user_id: Owner of the task.
            task_type: Classification string (ai_image, bulk_export, etc.).
            title: Human-readable description.
            func: Async callable accepting a TaskContext, returning a JSON-serializable result.
            timeout_seconds: Auto-cancel after this many seconds. 0 = no timeout.
            callback_url: Optional URL to POST when task completes.

        Returns:
            Dict with task_id and initial status.
        """
        task_id = str(uuid.uuid4())[:12]

        # Persist to database
        async with async_session() as session:
            db_task = BackgroundTask(
                task_id=task_id,
                user_id=user_id,
                task_type=task_type,
                title=title,
                status="pending",
                progress=0.0,
                timeout_seconds=timeout_seconds,
                callback_url=callback_url,
            )
            session.add(db_task)
            await session.commit()

        # Launch asyncio task
        ctx = TaskContext(task_id)
        asyncio_task = asyncio.create_task(
            self._run_task(task_id, ctx, func, timeout_seconds, callback_url)
        )
        self._running_tasks[task_id] = asyncio_task

        # Cleanup reference when done
        asyncio_task.add_done_callback(lambda _: self._running_tasks.pop(task_id, None))

        return {
            "task_id": task_id,
            "status": "pending",
            "task_type": task_type,
            "title": title,
        }

    async def _run_task(
        self,
        task_id: str,
        ctx: TaskContext,
        func: Callable,
        timeout_seconds: int,
        callback_url: Optional[str],
    ):
        """Execute the task function with timeout and status management."""
        # Mark as processing
        async with async_session() as session:
            await session.execute(
                update(BackgroundTask)
                .where(BackgroundTask.task_id == task_id)
                .values(status="processing", started_at=datetime.now(timezone.utc))
            )
            await session.commit()

        try:
            if timeout_seconds > 0:
                result = await asyncio.wait_for(func(ctx), timeout=timeout_seconds)
            else:
                result = await func(ctx)

            # Mark completed
            result_json = json.dumps(result) if result else None
            async with async_session() as session:
                await session.execute(
                    update(BackgroundTask)
                    .where(BackgroundTask.task_id == task_id)
                    .values(
                        status="completed",
                        progress=1.0,
                        result=result_json,
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()

            logger.info("Task %s completed successfully", task_id)

        except asyncio.TimeoutError:
            async with async_session() as session:
                await session.execute(
                    update(BackgroundTask)
                    .where(BackgroundTask.task_id == task_id)
                    .values(
                        status="failed",
                        error="Task timed out after %d seconds" % timeout_seconds,
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
            logger.warning("Task %s timed out after %ds", task_id, timeout_seconds)

        except asyncio.CancelledError:
            async with async_session() as session:
                await session.execute(
                    update(BackgroundTask)
                    .where(BackgroundTask.task_id == task_id)
                    .values(
                        status="cancelled",
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
            logger.info("Task %s was cancelled", task_id)

        except Exception as exc:
            async with async_session() as session:
                await session.execute(
                    update(BackgroundTask)
                    .where(BackgroundTask.task_id == task_id)
                    .values(
                        status="failed",
                        error=str(exc)[:1000],
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
            logger.exception("Task %s failed: %s", task_id, exc)

        # Fire callback webhook if configured
        if callback_url:
            await self._fire_callback(task_id, callback_url)

    async def _fire_callback(self, task_id: str, callback_url: str):
        """POST task result to the callback URL."""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(BackgroundTask).where(BackgroundTask.task_id == task_id)
                )
                task = result.scalar_one_or_none()
                if not task:
                    return

                payload = {
                    "task_id": task.task_id,
                    "status": task.status,
                    "result": json.loads(task.result) if task.result else None,
                    "error": task.error,
                }

            async with httpx.AsyncClient() as client:
                await client.post(callback_url, json=payload, timeout=10.0)
                logger.info("Callback sent for task %s to %s", task_id, callback_url)
        except Exception as exc:
            logger.warning("Failed to send callback for task %s: %s", task_id, exc)

    async def get_task_status(self, task_id: str, user_id: int) -> Optional[Dict]:
        """Get current status of a task."""
        async with async_session() as session:
            result = await session.execute(
                select(BackgroundTask).where(
                    BackgroundTask.task_id == task_id,
                    BackgroundTask.user_id == user_id,
                )
            )
            task = result.scalar_one_or_none()
            if not task:
                return None
            return self._task_to_dict(task)

    async def get_user_tasks(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict:
        """Get tasks for a user with optional status filter."""
        async with async_session() as session:
            query = select(BackgroundTask).where(BackgroundTask.user_id == user_id)
            if status:
                query = query.where(BackgroundTask.status == status)
            query = query.order_by(desc(BackgroundTask.created_at))

            # Count total
            from sqlalchemy import func
            count_query = select(func.count()).select_from(BackgroundTask).where(
                BackgroundTask.user_id == user_id
            )
            if status:
                count_query = count_query.where(BackgroundTask.status == status)
            total = (await session.execute(count_query)).scalar() or 0

            # Fetch page
            result = await session.execute(query.offset(offset).limit(limit))
            tasks = result.scalars().all()
            return {
                "items": [self._task_to_dict(t) for t in tasks],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def get_active_tasks(self, user_id: int) -> List[Dict]:
        """Get currently running/pending tasks for a user (for the progress indicator)."""
        async with async_session() as session:
            result = await session.execute(
                select(BackgroundTask)
                .where(
                    BackgroundTask.user_id == user_id,
                    or_(
                        BackgroundTask.status == "pending",
                        BackgroundTask.status == "processing",
                    ),
                )
                .order_by(desc(BackgroundTask.created_at))
            )
            tasks = result.scalars().all()
            return [self._task_to_dict(t) for t in tasks]

    async def cancel_task(self, task_id: str, user_id: int) -> bool:
        """Cancel a running task."""
        asyncio_task = self._running_tasks.get(task_id)
        if asyncio_task and not asyncio_task.done():
            asyncio_task.cancel()
            return True

        # Update DB for tasks that may not be running anymore
        async with async_session() as session:
            result = await session.execute(
                select(BackgroundTask).where(
                    BackgroundTask.task_id == task_id,
                    BackgroundTask.user_id == user_id,
                    or_(
                        BackgroundTask.status == "pending",
                        BackgroundTask.status == "processing",
                    ),
                )
            )
            task = result.scalar_one_or_none()
            if task:
                await session.execute(
                    update(BackgroundTask)
                    .where(BackgroundTask.task_id == task_id)
                    .values(status="cancelled", completed_at=datetime.now(timezone.utc))
                )
                await session.commit()
                return True
        return False

    async def cleanup_old_tasks(self):
        """Remove tasks older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=TASK_RETENTION_DAYS)
        async with async_session() as session:
            await session.execute(
                delete(BackgroundTask).where(
                    BackgroundTask.completed_at < cutoff,
                    or_(
                        BackgroundTask.status == "completed",
                        BackgroundTask.status == "failed",
                        BackgroundTask.status == "cancelled",
                    ),
                )
            )
            await session.commit()
        logger.info("Cleaned up old background tasks (older than %d days)", TASK_RETENTION_DAYS)

    @staticmethod
    def _task_to_dict(task: BackgroundTask) -> Dict:
        """Convert a BackgroundTask model to a dict."""
        result_data = None
        if task.result:
            try:
                result_data = json.loads(task.result)
            except (json.JSONDecodeError, TypeError):
                result_data = task.result

        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "title": task.title,
            "status": task.status,
            "progress": task.progress or 0.0,
            "result": result_data,
            "error": task.error,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "timeout_seconds": task.timeout_seconds,
        }


# Singleton instance
task_manager = TaskManager()
