"""工作流定义模型."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class NodeType(str, Enum):
    """节点类型."""

    SKILL = "skill"  # 调用 Skill
    CODE = "code"  # 执行代码
    TEMPLATE = "template"  # 模板渲染
    DECISION = "decision"  # 条件分支
    LOOP = "loop"  # 循环
    CHECKPOINT = "checkpoint"  # 人工检查点


class WorkflowInput(BaseModel):
    """工作流输入定义."""

    name: str = Field(..., description="输入参数名")
    type: str = Field(default="string", description="参数类型")
    required: bool = Field(default=True, description="是否必需")
    default: Any = Field(default=None, description="默认值")
    description: str = Field(default="", description="参数描述")


class WorkflowOutput(BaseModel):
    """工作流输出定义."""

    name: str = Field(..., description="输出名称")
    type: str = Field(default="string", description="输出类型")
    description: str = Field(default="", description="输出描述")
    source: str = Field(..., description="输出来源，如 ${node_id.output_name}")


class RetryPolicy(BaseModel):
    """重试策略."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_delay: float = Field(default=1.0, ge=0)
    max_delay: float = Field(default=60.0, ge=0)
    exponential_base: float = Field(default=2.0, ge=1.0)


class ErrorPolicy(BaseModel):
    """错误处理策略."""

    on_error: str = Field(
        default="pause",
        description="错误处理方式: pause(暂停), skip(跳过), fail(失败)",
    )
    retry: RetryPolicy = Field(default_factory=RetryPolicy)


class Node(BaseModel):
    """工作流节点."""

    id: str = Field(..., description="节点唯一标识")
    type: NodeType = Field(..., description="节点类型")
    name: str = Field(default="", description="节点可读名称")
    description: str = Field(default="", description="节点描述")

    # 类型特定配置
    skill_id: str | None = Field(default=None, description="Skill ID (type=skill)")
    skill_version: str | None = Field(default=None, description="Skill 版本")
    code: str | None = Field(default=None, description="代码内容 (type=code)")
    template: str | None = Field(default=None, description="模板内容 (type=template)")
    condition: str | None = Field(default=None, description="条件表达式 (type=decision)")
    max_iterations: int | None = Field(default=None, description="最大迭代次数 (type=loop)")

    # 输入配置
    inputs: dict[str, Any] = Field(default_factory=dict, description="节点输入")

    # 错误处理
    error_policy: ErrorPolicy = Field(default_factory=ErrorPolicy)

    # 执行控制
    timeout: int = Field(default=300, description="超时时间(秒)")

    @model_validator(mode="after")
    def validate_type_specific(self) -> "Node":
        """验证类型特定字段."""
        if self.type == NodeType.SKILL and not self.skill_id:
            raise ValueError("skill 类型节点必须指定 skill_id")
        if self.type == NodeType.CODE and not self.code:
            raise ValueError("code 类型节点必须指定 code")
        if self.type == NodeType.TEMPLATE and not self.template:
            raise ValueError("template 类型节点必须指定 template")
        if self.type == NodeType.DECISION and not self.condition:
            raise ValueError("decision 类型节点必须指定 condition")
        return self


class Edge(BaseModel):
    """工作流边（连接）."""

    from_node: str = Field(..., alias="from", description="源节点ID")
    to_node: str = Field(..., alias="to", description="目标节点ID")
    condition: str | None = Field(default=None, description="边条件（可选）")

    model_config = {"populate_by_name": True}


class WorkflowDefinition(BaseModel):
    """工作流定义."""

    # 基础信息
    id: str = Field(..., description="工作流唯一标识")
    name: str = Field(..., description="工作流名称")
    version: str = Field(default="1.0.0", description="工作流版本")
    description: str = Field(default="", description="工作流描述")

    # 输入输出契约
    inputs: list[WorkflowInput] = Field(default_factory=list)
    outputs: list[WorkflowOutput] = Field(default_factory=list)

    # 流程定义
    nodes: list[Node] = Field(..., description="节点列表")
    edges: list[Edge] = Field(default_factory=list, description="边列表")

    # 全局配置
    default_error_policy: ErrorPolicy = Field(default_factory=ErrorPolicy)

    @model_validator(mode="after")
    def validate_workflow(self) -> "WorkflowDefinition":
        """验证工作流完整性."""
        node_ids = {node.id for node in self.nodes}

        # 检查边的节点是否存在
        for edge in self.edges:
            if edge.from_node not in node_ids:
                raise ValueError(f"边引用了不存在的节点: {edge.from_node}")
            if edge.to_node not in node_ids:
                raise ValueError(f"边引用了不存在的节点: {edge.to_node}")

        # 检查输出引用
        for output in self.outputs:
            # 简单检查格式 ${node_id.output_name}
            if not output.source.startswith("${") or not output.source.endswith("}"):
                raise ValueError(f"输出 source 格式错误: {output.source}")

        return self

    def get_start_nodes(self) -> list[Node]:
        """获取起始节点（没有入边的节点）."""
        incoming = {edge.to_node for edge in self.edges}
        return [node for node in self.nodes if node.id not in incoming]

    def get_next_nodes(self, node_id: str) -> list[tuple[Node, str | None]]:
        """获取指定节点的后续节点及条件."""
        result = []
        for edge in self.edges:
            if edge.from_node == node_id:
                node = next((n for n in self.nodes if n.id == edge.to_node), None)
                if node:
                    result.append((node, edge.condition))
        return result

    def get_dependencies(self, node_id: str) -> list[Node]:
        """获取指定节点的依赖节点."""
        incoming = [edge.from_node for edge in self.edges if edge.to_node == node_id]
        return [n for n in self.nodes if n.id in incoming]
