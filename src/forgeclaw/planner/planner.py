"""规划服务实现."""

import json
import os
from datetime import datetime
from typing import Any

import httpx
import structlog

from forgeclaw.planner.models import (
    CostEstimate,
    EdgeDraft,
    LockedWorkflow,
    NodeDraft,
    PlanningResult,
    SkillInfo,
    UserFeedback,
    WorkflowDraft,
)
from forgeclaw.planner.prompts import (
    COST_ESTIMATION_PROMPT,
    MODIFICATION_SYSTEM_PROMPT,
    MODIFICATION_USER_PROMPT_TEMPLATE,
    PLANNING_SYSTEM_PROMPT,
    PLANNING_USER_PROMPT_TEMPLATE,
    RISK_ASSESSMENT_PROMPT,
)
from forgeclaw.skills.registry import SkillRegistry

logger = structlog.get_logger()


class PlannerService:
    """规划服务.

    负责：
    1. 分析用户目标，生成工作流草案
    2. 根据用户反馈修改草案
    3. 锁定工作流（形成契约）
    4. 成本预估和风险评估
    """

    def __init__(
        self,
        skill_registry: SkillRegistry | None = None,
        llm_api_key: str | None = None,
        llm_base_url: str | None = None,
        llm_model: str = "gpt-4o",
    ):
        self.skill_registry = skill_registry or SkillRegistry()
        self.llm_api_key = llm_api_key or os.getenv("OPENAI_API_KEY")
        self.llm_base_url = llm_base_url or "https://api.openai.com/v1"
        self.llm_model = llm_model
        
        # 锁定的工作流存储
        self._locked_workflows: dict[str, LockedWorkflow] = {}

    def _get_available_skills(self) -> list[SkillInfo]:
        """获取可用的 Skill 列表."""
        manifests = self.skill_registry.list_skills()
        return [
            SkillInfo(
                id=m.id,
                name=m.name,
                description=m.description,
                version=m.version,
                input_schema=m.input_schema,
                output_schema=m.output_schema,
            )
            for m in manifests
        ]

    def _format_skills_for_prompt(self, skills: list[SkillInfo]) -> str:
        """将 Skill 列表格式化为提示词."""
        lines = []
        for skill in skills:
            lines.append(f"- {skill.id}@{skill.version}: {skill.name}")
            lines.append(f"  描述: {skill.description}")
            if skill.input_schema:
                lines.append(f"  输入: {list(skill.input_schema.keys())}")
            if skill.output_schema:
                lines.append(f"  输出: {list(skill.output_schema.keys())}")
            lines.append("")
        return "\n".join(lines)

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> str:
        """调用 LLM API."""
        if not self.llm_api_key:
            raise ValueError("LLM API key not configured")

        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.llm_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """解析 LLM 的 JSON 响应."""
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                try:
                    return json.loads(response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # 尝试提取任意代码块
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                try:
                    return json.loads(response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        raise ValueError(f"无法解析 JSON 响应: {response[:200]}...")

    async def plan(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
    ) -> PlanningResult:
        """规划工作流.

        Args:
            goal: 用户目标描述
            context: 上下文信息

        Returns:
            规划结果
        """
        logger.info("planning_workflow", goal=goal)

        try:
            # 获取可用 Skill
            skills = self._get_available_skills()
            skills_text = self._format_skills_for_prompt(skills)

            # 构建提示词
            context_text = json.dumps(context, ensure_ascii=False, indent=2) if context else "无"
            user_prompt = PLANNING_USER_PROMPT_TEMPLATE.format(
                goal=goal,
                context=context_text,
                skills=skills_text,
            )

            # 调用 LLM
            response = await self._call_llm(
                system_prompt=PLANNING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
            )

            # 解析响应
            draft_data = self._parse_json_response(response)
            draft = WorkflowDraft(**draft_data)

            # 如果 LLM 没有提供成本预估，补充一个
            if draft.cost_estimate is None:
                draft.cost_estimate = await self._estimate_cost(draft)

            logger.info("planning_completed", workflow_name=draft.name, nodes_count=len(draft.nodes))

            return PlanningResult(
                success=True,
                draft=draft,
                raw_response=response,
            )

        except Exception as e:
            logger.error("planning_failed", error=str(e))
            return PlanningResult(
                success=False,
                error=str(e),
            )

    async def modify(
        self,
        current_draft: WorkflowDraft,
        feedback: UserFeedback,
    ) -> PlanningResult:
        """根据用户反馈修改工作流草案.

        Args:
            current_draft: 当前工作流草案
            feedback: 用户反馈

        Returns:
            修改后的规划结果
        """
        logger.info("modifying_workflow", action=feedback.action)

        if feedback.action == "confirm":
            # 用户确认，无需修改
            return PlanningResult(success=True, draft=current_draft)

        if feedback.action == "reject":
            # 用户拒绝
            return PlanningResult(
                success=False,
                error=f"用户拒绝: {feedback.feedback_text}",
            )

        try:
            # 获取可用 Skill
            skills = self._get_available_skills()
            skills_text = self._format_skills_for_prompt(skills)

            # 构建提示词
            current_draft_json = current_draft.model_dump_json(indent=2)
            modifications_json = json.dumps(feedback.modifications, ensure_ascii=False, indent=2)

            user_prompt = MODIFICATION_USER_PROMPT_TEMPLATE.format(
                current_draft=current_draft_json,
                action=feedback.action,
                feedback_text=feedback.feedback_text,
                modifications=modifications_json,
                skills=skills_text,
            )

            # 调用 LLM
            response = await self._call_llm(
                system_prompt=MODIFICATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
            )

            # 解析响应
            draft_data = self._parse_json_response(response)
            draft = WorkflowDraft(**draft_data)

            # 更新成本预估
            draft.cost_estimate = await self._estimate_cost(draft)

            logger.info("modification_completed", workflow_name=draft.name)

            return PlanningResult(
                success=True,
                draft=draft,
                raw_response=response,
            )

        except Exception as e:
            logger.error("modification_failed", error=str(e))
            return PlanningResult(
                success=False,
                error=str(e),
            )

    async def _estimate_cost(self, draft: WorkflowDraft) -> CostEstimate:
        """预估工作流成本."""
        # 简化版成本预估（不调用 LLM）
        total_tokens = 0
        total_cost = 0.0
        total_time = 0
        breakdown = []

        for node in draft.nodes:
            # 根据节点类型估算
            if node.type == "skill":
                tokens = 1000
                cost = 0.01
                time = 5
            elif node.type == "code":
                tokens = 100
                cost = 0.0
                time = 1
            elif node.type == "template":
                tokens = 200
                cost = 0.0
                time = 0.1
            elif node.type == "decision":
                tokens = 50
                cost = 0.0
                time = 0.1
            else:
                tokens = 500
                cost = 0.005
                time = 2

            total_tokens += tokens
            total_cost += cost
            total_time += time

            breakdown.append({
                "node_id": node.id,
                "node_type": node.type,
                "estimated_tokens": tokens,
                "estimated_cost_usd": cost,
                "estimated_time_seconds": time,
            })

        return CostEstimate(
            estimated_tokens=total_tokens,
            estimated_cost_usd=round(total_cost, 4),
            estimated_time_seconds=int(total_time),
            breakdown=breakdown,
        )

    async def lock(
        self,
        draft: WorkflowDraft,
        user_id: str | None = None,
    ) -> LockedWorkflow:
        """锁定工作流（形成契约）.

        Args:
            draft: 工作流草案
            user_id: 用户标识

        Returns:
            锁定的工作流
        """
        import shortuuid

        workflow_id = f"wf_{shortuuid.uuid()}"
        locked_at = datetime.utcnow().isoformat()

        locked = LockedWorkflow(
            workflow_id=workflow_id,
            draft=draft,
            locked_at=locked_at,
            locked_by=user_id,
            version="1.0.0",
            planning_history=[{
                "action": "lock",
                "timestamp": locked_at,
                "user_id": user_id,
            }],
        )

        self._locked_workflows[workflow_id] = locked

        logger.info("workflow_locked", workflow_id=workflow_id, user_id=user_id)

        return locked

    async def get_locked(self, workflow_id: str) -> LockedWorkflow | None:
        """获取锁定的工作流."""
        return self._locked_workflows.get(workflow_id)

    async def unlock(
        self,
        workflow_id: str,
        reason: str,
        user_id: str | None = None,
    ) -> bool:
        """解锁工作流（用于修改）."""
        locked = self._locked_workflows.get(workflow_id)
        if not locked:
            return False

        # 创建新版本
        locked.planning_history.append({
            "action": "unlock",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "reason": reason,
        })

        logger.info("workflow_unlocked", workflow_id=workflow_id, reason=reason)
        return True

    async def list_locked(self) -> list[LockedWorkflow]:
        """列出所有锁定的工作流."""
        return list(self._locked_workflows.values())

    def draft_to_workflow_definition(self, draft: WorkflowDraft) -> dict[str, Any]:
        """将草案转换为工作流定义（用于执行引擎）."""
        from forgeclaw.models.workflow import Edge, Node, NodeType, WorkflowDefinition

        # 转换节点
        nodes = []
        for node_draft in draft.nodes:
            node_type = NodeType(node_draft.type)
            node_kwargs = dict(
                id=node_draft.id,
                type=node_type,
                name=node_draft.name,
                description=node_draft.description,
                inputs=node_draft.inputs,
            )
            
            if node_type == NodeType.SKILL:
                node_kwargs["skill_id"] = node_draft.skill_id
                node_kwargs["skill_version"] = node_draft.skill_version
            elif node_type == NodeType.CODE:
                # 从 inputs 中提取 code
                code = node_draft.inputs.get("code", "")
                node_kwargs["code"] = code
            elif node_type == NodeType.TEMPLATE:
                # 从 inputs 中提取 template（如果有）
                template = node_draft.inputs.get("template", "")
                node_kwargs["template"] = template
            
            node = Node(**node_kwargs)
            nodes.append(node)

        # 转换边
        edges = [
            Edge(from_node=e.from_node, to_node=e.to_node, condition=e.condition)
            for e in draft.edges
        ]

        # 创建工作流定义
        return {
            "id": f"draft_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "name": draft.name,
            "description": draft.description,
            "version": draft.version,
            "nodes": [n.model_dump() for n in nodes],
            "edges": [e.model_dump() for e in edges],
            "inputs": draft.inputs,
            "outputs": draft.outputs,
        }
