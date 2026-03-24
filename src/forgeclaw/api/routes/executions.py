"""执行路由."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from forgeclaw.engine.executor import WorkflowExecutor
from forgeclaw.models.execution import ExecutionResult, ExecutionStatus
from forgeclaw.models.workflow import WorkflowDefinition

router = APIRouter()
executor = WorkflowExecutor()

# 引用工作流存储（实际应用应使用数据库）
from forgeclaw.api.routes import workflows


class ExecuteRequest(BaseModel):
    """执行请求."""
    inputs: dict[str, Any] = {}


@router.post("/{workflow_id}", response_model=dict)
async def execute_workflow(workflow_id: str, request: ExecuteRequest) -> dict[str, Any]:
    """执行工作流."""
    if workflow_id not in workflows._workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows._workflows[workflow_id]
    result = await executor.execute(workflow, request.inputs)
    
    return {
        "execution_id": result.execution_id,
        "status": result.status,
        "outputs": result.outputs,
    }


@router.get("/status/{execution_id}", response_model=dict)
async def get_execution_status(execution_id: str) -> dict[str, Any]:
    """获取执行状态."""
    from forgeclaw.engine.state import ExecutionStateManager
    
    state_manager = ExecutionStateManager()
    state = await state_manager.load_state(execution_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "execution_id": state.execution_id,
        "status": state.status,
        "workflow_id": state.workflow_id,
        "current_nodes": state.current_nodes,
        "completed_nodes": state.completed_nodes,
    }


@router.post("/control/{execution_id}/pause", response_model=dict)
async def pause_execution(execution_id: str) -> dict[str, Any]:
    """暂停执行."""
    await executor.pause(execution_id)
    return {"execution_id": execution_id, "action": "pause", "status": "requested"}


@router.post("/control/{execution_id}/resume", response_model=dict)
async def resume_execution(execution_id: str) -> dict[str, Any]:
    """恢复执行."""
    await executor.resume(execution_id)
    return {"execution_id": execution_id, "action": "resume", "status": "requested"}


@router.post("/control/{execution_id}/terminate", response_model=dict)
async def terminate_execution(execution_id: str) -> dict[str, Any]:
    """终止执行."""
    await executor.terminate(execution_id)
    return {"execution_id": execution_id, "action": "terminate", "status": "requested"}
