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

# 执行记录存储（MVP 内存存储）
_execution_history: dict[str, dict[str, Any]] = {}


class ExecuteRequest(BaseModel):
    """执行请求."""
    inputs: dict[str, Any] = {}


class StartExecutionRequest(BaseModel):
    """启动执行请求."""
    workflow_id: str
    inputs: dict[str, Any] = {}


@router.post("/start", response_model=dict)
async def start_execution(request: StartExecutionRequest) -> dict[str, Any]:
    """启动工作流执行 (前端兼容格式)."""
    if request.workflow_id not in workflows._workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows._workflows[request.workflow_id]
    result = await executor.execute(workflow, request.inputs)
    
    # 存储执行记录
    _execution_history[result.execution_id] = {
        "execution_id": result.execution_id,
        "workflow_id": request.workflow_id,
        "status": result.status,
        "inputs": request.inputs,
        "outputs": result.outputs,
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "logs": getattr(result, 'logs', []),
        "node_results": getattr(result, 'node_results', []),
        "completed_nodes": getattr(result, 'completed_nodes', []),
    }
    
    return {
        "execution_id": result.execution_id,
        "status": result.status,
        "workflow_id": request.workflow_id,
    }


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


@router.get("", response_model=list)
async def list_executions() -> list[dict[str, Any]]:
    """列出所有执行记录."""
    return list(_execution_history.values())


@router.get("/{execution_id}", response_model=dict)
async def get_execution(execution_id: str) -> dict[str, Any]:
    """获取执行详情."""
    if execution_id in _execution_history:
        return _execution_history[execution_id]
    
    # 如果不在历史记录中，尝试从状态管理器获取
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


@router.post("/{execution_id}/pause", response_model=dict)
async def pause_execution_v2(execution_id: str) -> dict[str, Any]:
    """暂停执行 (前端兼容格式)."""
    await executor.pause(execution_id)
    return {"execution_id": execution_id, "action": "pause", "status": "requested"}


@router.post("/{execution_id}/resume", response_model=dict)
async def resume_execution_v2(execution_id: str) -> dict[str, Any]:
    """恢复执行 (前端兼容格式)."""
    await executor.resume(execution_id)
    return {"execution_id": execution_id, "action": "resume", "status": "requested"}


@router.post("/{execution_id}/terminate", response_model=dict)
async def terminate_execution_v2(execution_id: str) -> dict[str, Any]:
    """终止执行 (前端兼容格式)."""
    await executor.terminate(execution_id)
    return {"execution_id": execution_id, "action": "terminate", "status": "requested"}


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
