"""工作流路由."""

from typing import Any

from fastapi import APIRouter, HTTPException

from forgeclaw.models.workflow import WorkflowDefinition

router = APIRouter()

# 内存存储（MVP）
_workflows: dict[str, WorkflowDefinition] = {}


@router.post("", response_model=dict)
async def create_workflow(workflow: WorkflowDefinition) -> dict[str, Any]:
    """创建工作流."""
    if workflow.id in _workflows:
        raise HTTPException(status_code=409, detail="Workflow already exists")
    
    _workflows[workflow.id] = workflow
    return {"id": workflow.id, "status": "created"}


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str) -> WorkflowDefinition:
    """获取工作流."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflows[workflow_id]


@router.get("", response_model=list)
async def list_workflows() -> list[dict[str, Any]]:
    """列出所有工作流."""
    return [
        {"id": wf.id, "name": wf.name, "version": wf.version}
        for wf in _workflows.values()
    ]


@router.put("/{workflow_id}", response_model=dict)
async def update_workflow(workflow_id: str, workflow: WorkflowDefinition) -> dict[str, Any]:
    """更新工作流."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    _workflows[workflow_id] = workflow
    return {"id": workflow_id, "status": "updated"}


@router.delete("/{workflow_id}", response_model=dict)
async def delete_workflow(workflow_id: str) -> dict[str, Any]:
    """删除工作流."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del _workflows[workflow_id]
    return {"id": workflow_id, "status": "deleted"}
