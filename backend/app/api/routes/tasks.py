"""Background Tasks API routes.

Provides endpoints to:
- Query status of individual tasks
- List active (pending/processing) tasks for the progress indicator
- List task history with optional status filter
- Cancel running tasks
- Submit demo/test tasks (for verification)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.task_manager import task_manager, TaskContext

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get current status of a specific background task.

    Returns task_id, status, progress (0.0-1.0), result/error, and timestamps.
    """
    task = await task_manager.get_task_status(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/active")
async def get_active_tasks(
    user_id: int = Depends(get_current_user_id),
):
    """Get all currently pending/processing tasks for the current user.

    Used by the frontend ProgressIndicator to show ongoing operations.
    """
    tasks = await task_manager.get_active_tasks(user_id)
    return {"tasks": tasks, "count": len(tasks)}


@router.get("/history")
async def get_task_history(
    status: Optional[str] = Query(None, description="Filter by status: pending, processing, completed, failed, cancelled"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user_id),
):
    """Get task history for the current user.

    Supports filtering by status and pagination. Returns last N tasks
    ordered by creation date (newest first).
    """
    valid_statuses = {"pending", "processing", "completed", "failed", "cancelled"}
    if status and status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}"
        )
    return await task_manager.get_user_tasks(user_id, status=status, limit=limit, offset=offset)


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Cancel a pending or processing task.

    Returns success if the task was cancelled, or an error if it cannot be cancelled
    (e.g., already completed or not found).
    """
    cancelled = await task_manager.cancel_task(task_id, user_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Task cannot be cancelled (may be already completed or not found)"
        )
    return {"task_id": task_id, "status": "cancelled", "message": "Task cancelled successfully"}


@router.post("/submit-demo")
async def submit_demo_task(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Submit a demo background task for testing/verification.

    Simulates a long-running operation with configurable duration and progress updates.

    Body:
        title: str - Task title (default: "Demo-Task")
        duration_seconds: int - How long the task runs (default: 10, max: 60)
        should_fail: bool - If true, the task will fail after 50% progress (default: false)
    """
    title = request.get("title", "Demo-Task")
    duration = min(request.get("duration_seconds", 10), 60)
    should_fail = request.get("should_fail", False)

    async def demo_operation(ctx: TaskContext):
        """Simulated long-running operation."""
        steps = 10
        for i in range(steps):
            ctx.check_cancelled()
            await asyncio.sleep(duration / steps)
            progress = (i + 1) / steps
            await ctx.update_progress(progress, f"Schritt {i+1}/{steps}")
            if should_fail and progress >= 0.5:
                raise RuntimeError("Demo-Task absichtlich fehlgeschlagen bei 50%")
        return {"message": "Demo-Task erfolgreich abgeschlossen", "steps_completed": steps}

    result = await task_manager.submit_task(
        user_id=user_id,
        task_type="demo",
        title=title,
        func=demo_operation,
        timeout_seconds=max(duration + 10, 30),
    )
    return result


@router.post("/cleanup")
async def cleanup_old_tasks(
    user_id: int = Depends(get_current_user_id),
):
    """Manually trigger cleanup of old completed/failed tasks.

    Removes tasks older than the retention period (7 days by default).
    """
    await task_manager.cleanup_old_tasks()
    return {"message": "Old tasks cleaned up successfully"}
