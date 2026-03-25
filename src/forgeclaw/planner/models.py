"""规划服务模型."""

from typing import Any

from pydantic import BaseModel, Field


class SkillInfo(BaseModel):
    """Skill 信息（用于规划时展示给 LLM）."""

    id: str
    name: str
    description: str
    version: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class NodeDraft(BaseModel):
    """节点草案."""

    id: str = Field(description="节点唯一标识")
    type: str = Field(description="节点类型: skill, code, template, decision")
    name: str = Field(description="节点可读名称")
    description: str = Field(description="节点功能描述")
    skill_id: str | None = Field(default=None, description="引用的 Skill ID")
    skill_version: str | None = Field(default=None, description="Skill 版本")
    inputs: dict[str, Any] = Field(default_factory=dict, description="节点输入配置")
    temperature: float = Field(default=0.5, ge=0.0, le=1.0, description="发散程度 (0-1)")


class EdgeDraft(BaseModel):
    """边草案."""

    from_node: str = Field(alias="from", description="源节点ID")
    to_node: str = Field(alias="to", description="目标节点ID")
    condition: str | None = Field(default=None, description="条件表达式")

    model_config = {"populate_by_name": True}


class CostEstimate(BaseModel):
    """成本预估."""

    estimated_tokens: int = Field(description="预估 Token 数量")
    estimated_cost_usd: float = Field(description="预估成本 (USD)")
    estimated_time_seconds: int = Field(description="预估执行时间 (秒)")
    estimated_time_minutes: int = Field(default=0, description="预估执行时间 (分钟)")
    breakdown: list[dict[str, Any]] = Field(default_factory=list, description="成本明细")
    
    def model_post_init(self, __context: Any) -> None:
        """计算分钟数."""
        self.estimated_time_minutes = self.estimated_time_seconds // 60


class Analysis4W1H(BaseModel):
    """4W1H 分析结果."""
    
    what: str = Field(description="要做什么")
    why: str = Field(description="为什么做")
    who: str = Field(description="涉及哪些 Skill")
    when: str = Field(description="执行时机")
    how: str = Field(description="如何执行")


class WorkflowDraft(BaseModel):
    """工作流草案."""

    id: str = Field(default="", description="草案唯一标识")
    name: str = Field(description="工作流名称")
    description: str = Field(description="工作流描述")
    version: str = Field(default="1.0.0", description="版本")
    
    # 4W1H 分析（兼容旧格式）
    analysis: Analysis4W1H | None = Field(default=None, description="4W1H 分析")
    
    # 直接在 draft 上的 4W1H 字段（向后兼容）
    what: str = Field(default="", description="要做什么")
    why: str = Field(default="", description="为什么做")
    who: str = Field(default="", description="涉及哪些 Skill")
    when: str = Field(default="", description="执行时机")
    how: str = Field(default="", description="如何执行")
    
    # 流程定义
    nodes: list[NodeDraft] = Field(default_factory=list, description="节点列表")
    edges: list[EdgeDraft] = Field(default_factory=list, description="边列表")
    
    # 输入输出
    inputs: list[dict[str, Any]] = Field(default_factory=list, description="输入定义")
    outputs: list[dict[str, Any]] = Field(default_factory=list, description="输出定义")
    
    # 成本预估
    cost_estimate: CostEstimate | None = Field(default=None, description="成本预估")
    
    # 风险提示
    risk_level: str = Field(default="low", description="风险等级: low/medium/high")
    risk_notes: list[str] = Field(default_factory=list, description="风险说明")


class RiskAssessment(BaseModel):
    """风险评估."""
    
    type: str = Field(description="风险类型")
    severity: str = Field(description="严重程度: low/medium/high")
    description: str = Field(description="风险描述")
    mitigation: str = Field(description="缓解措施")


class PlanningResult(BaseModel):
    """规划结果."""

    success: bool = Field(description="是否成功")
    draft: WorkflowDraft | None = Field(default=None, description="工作流草案")
    error: str | None = Field(default=None, description="错误信息")
    raw_response: str | None = Field(default=None, description="LLM 原始响应")
    risk_assessment: list[RiskAssessment] = Field(default_factory=list, description="风险评估")


class UserFeedback(BaseModel):
    """用户反馈（用于修改草案）."""

    action: str = Field(description="操作: confirm/modify/reject")
    modifications: dict[str, Any] = Field(default_factory=dict, description="修改内容")
    feedback_text: str = Field(default="", description="用户反馈文本")


class LockedWorkflow(BaseModel):
    """锁定的工作流（契约）."""

    workflow_id: str = Field(description="工作流唯一标识")
    draft: WorkflowDraft = Field(description="锁定的工作流草案")
    locked_at: str = Field(description="锁定时间")
    locked_by: str | None = Field(default=None, description="锁定者")
    
    # 版本控制
    version: str = Field(default="1.0.0", description="版本")
    parent_version: str | None = Field(default=None, description="父版本")
    
    # 审计
    planning_history: list[dict[str, Any]] = Field(default_factory=list, description="规划历史")
    user_feedback_history: list[UserFeedback] = Field(default_factory=list, description="用户反馈历史")
