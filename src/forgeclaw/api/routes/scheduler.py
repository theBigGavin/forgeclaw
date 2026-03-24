"""定时任务路由."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from forgeclaw.scheduler.models import ScheduledTask
from forgeclaw.scheduler.scheduler import ScheduleService

router = APIRouter()
scheduler = ScheduleService()


class CreateTaskRequest(BaseModel):
    """创建任务请求."""
    task: ScheduledTask


class UpdateTaskRequest(BaseModel):
    """更新任务请求."""
    updates: dict[str, Any]


@router.post("", response_model=dict)
async def create_task(request: CreateTaskRequest) -> dict[str, Any]:
    """创建定时任务."""
    task_id = await scheduler.create_task(request.task)
    return {"task_id": task_id, "status": "created"}


@router.get("", response_model=list)
async def list_tasks(enabled_only: bool = False) -> list[dict[str, Any]]:
    """列出定时任务."""
    tasks = await scheduler.list_tasks(enabled_only=enabled_only)
    return [
        {
            "id": t.id,
            "name": t.name,
            "enabled": t.enabled,
            "trigger_type": t.trigger_type,
            "last_run_status": t.last_run_status,
            "next_run_at": t.next_run_at,
        }
        for t in tasks
    ]


@router.get("/{task_id}", response_model=ScheduledTask)
async def get_task(task_id: str) -> ScheduledTask:
    """获取任务详情."""
    task = await scheduler.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=dict)
async def update_task(task_id: str, request: UpdateTaskRequest) -> dict[str, Any]:
    """更新任务."""
    success = await scheduler.update_task(task_id, request.updates)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": "updated"}


@router.delete("/{task_id}", response_model=dict)
async def delete_task(task_id: str) -> dict[str, Any]:
    """删除任务."""
    success = await scheduler.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": "deleted"}


@router.post("/{task_id}/trigger", response_model=dict)
async def trigger_task(task_id: str) -> dict[str, Any]:
    """手动触发任务."""
    result = await scheduler.trigger_task(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": "triggered"}


@router.get("/{task_id}/records", response_model=list)
async def get_execution_records(task_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """获取执行记录."""
    records = await scheduler.get_execution_records(task_id, limit)
    return [r.model_dump() for r in records]
