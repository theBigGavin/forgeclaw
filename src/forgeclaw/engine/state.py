"""执行状态管理."""

import json
from pathlib import Path
from typing import Any

import structlog

from forgeclaw.models.execution import ExecutionState

logger = structlog.get_logger()


class ExecutionStateManager:
    """执行状态管理器.

    MVP 使用文件存储，后续可替换为数据库.
    """

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or ".forgeclaw/executions")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def save_state(self, state: ExecutionState) -> None:
        """保存执行状态."""
        file_path = self.storage_path / f"{state.execution_id}.json"
        
        # 使用 Pydantic 的 model_dump
        data = state.model_dump(mode="json")
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.debug("state_saved", execution_id=state.execution_id, path=str(file_path))

    async def load_state(self, execution_id: str) -> ExecutionState | None:
        """加载执行状态."""
        file_path = self.storage_path / f"{execution_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path) as f:
            data = json.load(f)
        
        return ExecutionState(**data)

    async def list_states(self) -> list[str]:
        """列出所有执行状态."""
        return [f.stem for f in self.storage_path.glob("*.json")]

    async def delete_state(self, execution_id: str) -> bool:
        """删除执行状态."""
        file_path = self.storage_path / f"{execution_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            logger.info("state_deleted", execution_id=execution_id)
            return True
        return False
