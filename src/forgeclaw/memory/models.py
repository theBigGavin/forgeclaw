"""记忆系统模型."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """记忆类型."""

    WORKFLOW = "workflow"  # 工作流执行记录
    SKILL = "skill"  # Skill 调用记录
    ASSET = "asset"  # 生成的资产
    CONVERSATION = "conversation"  # 对话记录
    DECISION = "decision"  # 决策记录
    SCHEDULED = "scheduled"  # 定时任务执行


class WorkflowMemoryContent(BaseModel):
    """工作流记忆内容."""

    workflow_id: str
    execution_id: str
    status: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    node_results: dict[str, Any] = Field(default_factory=dict)


class SkillMemoryContent(BaseModel):
    """Skill 记忆内容."""

    skill_id: str
    skill_version: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: int = 0


class AssetMemoryContent(BaseModel):
    """资产记忆内容."""

    asset_id: str
    asset_type: str
    name: str
    description: str
    storage_path: str
    size_bytes: int
    created_by: str  # 工作流/节点 ID
    lineage: dict[str, Any] = Field(default_factory=dict)  # 生成链路


class ConversationMemoryContent(BaseModel):
    """对话记忆内容."""

    session_id: str
    user_message: str
    assistant_message: str
    context: dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    """记忆条目."""

    id: str = Field(..., description="记忆唯一标识")
    type: MemoryType = Field(..., description="记忆类型")

    # 关联信息
    workflow_id: str | None = Field(default=None, description="关联工作流 ID")
    execution_id: str | None = Field(default=None, description="关联执行 ID")
    project_id: str | None = Field(default=None, description="关联项目 ID")
    session_id: str | None = Field(default=None, description="关联会话 ID")

    # 内容（根据类型不同）
    content: dict[str, Any] = Field(default_factory=dict, description="记忆内容")

    # 关系图谱
    related_workflows: list[str] = Field(default_factory=list, description="关联工作流")
    related_skills: list[str] = Field(default_factory=list, description="关联 Skill")
    related_assets: list[str] = Field(default_factory=list, description="关联资产")
    parent_memory: str | None = Field(default=None, description="父记忆 ID")
    child_memories: list[str] = Field(default_factory=list, description="子记忆 ID")

    # 时间信息
    created_at: str = Field(..., description="创建时间")
    updated_at: str | None = Field(default=None, description="更新时间")

    # 向量嵌入（用于语义检索）
    embedding: list[float] | None = Field(default=None, description="向量嵌入")

    # 元数据
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class MemoryQuery(BaseModel):
    """记忆查询."""

    # 精确查询
    memory_id: str | None = None
    memory_type: MemoryType | None = None
    workflow_id: str | None = None
    execution_id: str | None = None
    project_id: str | None = None

    # 时间范围
    start_time: str | None = None
    end_time: str | None = None

    # 语义查询
    semantic_query: str | None = None
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    top_k: int = Field(default=5, ge=1, le=100)

    # 关系查询
    related_to: str | None = None  # 查询与此记忆相关的记忆
    relation_depth: int = Field(default=1, ge=1, le=5)

    # 分页
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ContextSnapshot(BaseModel):
    """上下文快照（用于注入工作流）."""

    snapshot_id: str
    project_id: str | None = None
    session_id: str | None = None

    # 最近的记忆
    recent_memories: list[MemoryEntry] = Field(default_factory=list)

    # 相关记忆（按语义检索）
    relevant_memories: list[MemoryEntry] = Field(default_factory=list)

    # 项目级记忆
    project_memories: list[MemoryEntry] = Field(default_factory=list)

    # 汇总信息
    summary: str = Field(default="", description="上下文摘要")

    created_at: str = Field(..., description="快照创建时间")
