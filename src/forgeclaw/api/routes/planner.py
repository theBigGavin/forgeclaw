"""规划服务路由."""

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from forgeclaw.planner.models import (
    LockedWorkflow,
    PlanningResult,
    PlanningTaskStatus,
    UserFeedback,
    WorkflowDraft,
)
from forgeclaw.planner.planner import PlannerService

router = APIRouter()

# 延迟初始化，确保环境变量已加载
_planner: PlannerService | None = None


def get_planner() -> PlannerService:
    """获取 PlannerService 实例（延迟初始化）."""
    global _planner
    if _planner is None:
        _planner = PlannerService()
    return _planner


class PlanRequest(BaseModel):
    """规划请求."""
    goal: str
    context: dict[str, Any] | None = None


class ModifyRequest(BaseModel):
    """修改请求."""
    current_draft: WorkflowDraft
    feedback: UserFeedback


class LockRequest(BaseModel):
    """锁定请求."""
    draft: WorkflowDraft
    user_id: str | None = None


@router.post("/plan", response_model=PlanningResult)
async def plan_workflow(request: PlanRequest) -> PlanningResult:
    """规划工作流（同步，保持兼容）.

    根据用户目标生成工作流草案。
    """
    result = await get_planner().plan(request.goal, request.context)
    return result


@router.post("/plan-async", response_model=dict[str, str])
async def plan_workflow_async(request: PlanRequest) -> dict[str, str]:
    """异步规划工作流.
    
    立即返回任务ID，后台异步执行规划。
    使用 GET /plan-tasks/{task_id} 查询进度。
    """
    task_id = await get_planner().plan_async(request.goal, request.context)
    return {"task_id": task_id, "status": "accepted"}


@router.get("/plan-tasks/{task_id}", response_model=PlanningTaskStatus)
async def get_planning_task_status(task_id: str) -> PlanningTaskStatus:
    """获取异步规划任务状态."""
    task = get_planner().get_planning_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/plan-tasks", response_model=list[PlanningTaskStatus])
async def list_planning_tasks() -> list[PlanningTaskStatus]:
    """列出所有异步规划任务."""
    return get_planner().list_planning_tasks()


@router.post("/modify", response_model=PlanningResult)
async def modify_workflow(request: ModifyRequest) -> PlanningResult:
    """修改工作流草案.

    根据用户反馈修改工作流。
    """
    result = await get_planner().modify(request.current_draft, request.feedback)
    return result


@router.post("/lock", response_model=LockedWorkflow)
async def lock_workflow(request: LockRequest) -> LockedWorkflow:
    """锁定工作流.

    将工作流草案锁定为可执行的契约。
    """
    locked = await get_planner().lock(request.draft, request.user_id)
    return locked


@router.post("/confirm/{draft_id}", response_model=LockedWorkflow)
async def confirm_workflow(draft_id: str, user_id: str | None = None) -> LockedWorkflow:
    """确认并锁定工作流草案.
    
    根据 draft_id 查找缓存的草案并锁定。
    """
    try:
        locked = await get_planner().confirm(draft_id, user_id)
        return locked
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/locked/{workflow_id}", response_model=LockedWorkflow)
async def get_locked_workflow(workflow_id: str) -> LockedWorkflow:
    """获取锁定的工作流."""
    locked = await get_planner().get_locked(workflow_id)
    if not locked:
        raise HTTPException(status_code=404, detail="Locked workflow not found")
    return locked


@router.get("/locked", response_model=list[LockedWorkflow])
async def list_locked_workflows() -> list[LockedWorkflow]:
    """列出所有锁定的工作流."""
    return await get_planner().list_locked()


@router.post("/estimate", response_model=dict[str, Any])
async def estimate_cost(draft: WorkflowDraft) -> dict[str, Any]:
    """预估工作流成本.

    重新计算工作流的成本预估。
    """
    cost = await get_planner()._estimate_cost(draft)
    return cost.model_dump()
