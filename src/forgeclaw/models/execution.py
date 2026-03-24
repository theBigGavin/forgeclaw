"""执行相关模型."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """执行状态."""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    PAUSED = "paused"  # 暂停（人工介入）
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败
    TERMINATED = "terminated"  # 终止


class NodeExecutionStatus(str, Enum):
    """节点执行状态."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class NodeExecutionResult(BaseModel):
    """单个节点执行结果."""

    node_id: str
    status: NodeExecutionStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    attempt: int = 1  # 当前尝试次数
    logs: list[str] = Field(default_factory=list)


class ExecutionContext(BaseModel):
    """执行上下文."""

    execution_id: str
    workflow_id: str

    # 输入数据
    inputs: dict[str, Any] = Field(default_factory=dict)

    # 节点输出（供后续节点引用）
    node_outputs: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # 变量存储
    variables: dict[str, Any] = Field(default_factory=dict)

    # 执行元数据
    start_time: str | None = None
    user_id: str | None = None


class ExecutionState(BaseModel):
    """执行状态（可持久化）."""

    execution_id: str
    workflow_id: str
    status: ExecutionStatus

    # 节点执行状态
    node_states: dict[str, NodeExecutionResult] = Field(default_factory=dict)

    # 当前执行位置
    current_nodes: list[str] = Field(default_factory=list)
    completed_nodes: list[str] = Field(default_factory=list)

    # 上下文快照
    context: ExecutionContext

    # 时间戳
    start_time: str | None = None
    end_time: str | None = None

    # 成本追踪
    tokens_used: int = 0
    estimated_cost: float = 0.0


class ExecutionResult(BaseModel):
    """执行结果."""

    execution_id: str
    status: ExecutionStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    node_results: dict[str, NodeExecutionResult] = Field(default_factory=dict)
    start_time: str | None = None
    end_time: str | None = None
    tokens_used: int = 0
    estimated_cost: float = 0.0
