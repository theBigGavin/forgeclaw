"""定时任务路由."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from forgeclaw.scheduler.models import ScheduledTask, TriggerType, ContextInheritancePolicy
from forgeclaw.scheduler.scheduler import ScheduleService

router = APIRouter()
scheduler = ScheduleService()


class CreateTaskRequest(BaseModel):
    """创建任务请求."""
    task: ScheduledTask


class CreateTaskSimpleRequest(BaseModel):
    """创建任务请求 (前端兼容格式)."""
    name: str
    workflow_id: str
    trigger: dict[str, Any]
    context_policy: str = "recent"


class UpdateTaskRequest(BaseModel):
    """更新任务请求."""
    updates: dict[str, Any]


# ========== 基础路由 ==========

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
            "trigger_type": t.trigger_type.value if hasattr(t.trigger_type, 'value') else str(t.trigger_type),
            "trigger": t.trigger,
            "context_policy": t.context_policy.value if hasattr(t.context_policy, 'value') else str(t.context_policy),
            "last_run_status": t.last_run_status,
            "next_run_at": t.next_run_at,
            "workflow_id": t.workflow_id,
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


@router.patch("/{task_id}", response_model=dict)
async def update_task_patch(task_id: str, request: UpdateTaskRequest) -> dict[str, Any]:
    """更新任务 (PATCH 方法，前端兼容)."""
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


# ========== /tasks 别名路由 (前端兼容) ==========

@router.post("/tasks", response_model=dict)
async def create_task_alias(request: CreateTaskSimpleRequest) -> dict[str, Any]:
    """创建定时任务 (前端兼容格式)."""
    # 转换前端格式为内部格式
    trigger_type = request.trigger.get("type", "interval")
    trigger_config = request.trigger.get("config", {})
    
    # 构建 ScheduledTask
    task = ScheduledTask(
        id="",  # 由 scheduler 生成
        name=request.name,
        workflow_id=request.workflow_id,
        trigger_type=TriggerType(trigger_type),
        trigger=trigger_config,
        context_policy=ContextInheritancePolicy(request.context_policy),
        enabled=True,
    )
    
    task_id = await scheduler.create_task(task)
    return {"id": task_id, "status": "created"}


@router.get("/tasks", response_model=list)
async def list_tasks_alias(enabled_only: bool = False) -> list[dict[str, Any]]:
    """列出定时任务 (前端兼容)."""
    return await list_tasks(enabled_only=enabled_only)


@router.patch("/tasks/{task_id}", response_model=dict)
async def update_task_patch_alias(task_id: str, request: UpdateTaskRequest) -> dict[str, Any]:
    """更新任务 (前端兼容 PATCH 方法)."""
    return await update_task_patch(task_id, request)


@router.delete("/tasks/{task_id}", response_model=dict)
async def delete_task_alias(task_id: str) -> dict[str, Any]:
    """删除任务 (前端兼容)."""
    return await delete_task(task_id)
