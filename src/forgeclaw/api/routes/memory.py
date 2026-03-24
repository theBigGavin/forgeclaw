"""记忆服务路由."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from forgeclaw.memory.memory_service import MemoryService
from forgeclaw.memory.models import MemoryEntry, MemoryQuery

router = APIRouter()
memory_service = MemoryService()


class StoreRequest(BaseModel):
    """存储请求."""
    entry: MemoryEntry


class QueryRequest(BaseModel):
    """查询请求."""
    query: MemoryQuery


class BuildContextRequest(BaseModel):
    """构建上下文请求."""
    project_id: str | None = None
    session_id: str | None = None
    workflow_id: str | None = None
    semantic_query: str | None = None


@router.post("/store", response_model=dict)
async def store_memory(request: StoreRequest) -> dict[str, Any]:
    """存储记忆."""
    memory_id = await memory_service.store(request.entry)
    return {"memory_id": memory_id, "status": "stored"}


@router.get("/{memory_id}", response_model=MemoryEntry)
async def get_memory(memory_id: str) -> MemoryEntry:
    """获取记忆."""
    entry = await memory_service.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory not found")
    return entry


@router.post("/query", response_model=list[MemoryEntry])
async def query_memory(request: QueryRequest) -> list[MemoryEntry]:
    """查询记忆."""
    results = await memory_service.query(request.query)
    return results


@router.post("/context", response_model=dict)
async def build_context(request: BuildContextRequest) -> dict[str, Any]:
    """构建上下文快照."""
    snapshot = await memory_service.build_context(
        project_id=request.project_id,
        session_id=request.session_id,
        workflow_id=request.workflow_id,
        semantic_query=request.semantic_query,
    )
    return snapshot.model_dump()


@router.delete("/{memory_id}", response_model=dict)
async def delete_memory(memory_id: str) -> dict[str, Any]:
    """删除记忆."""
    success = await memory_service.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"memory_id": memory_id, "status": "deleted"}
