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
        llm_model: str | None = None,
    ):
        self.skill_registry = skill_registry or SkillRegistry()
        self.llm_api_key = llm_api_key or os.getenv("OPENAI_API_KEY")
        self.llm_base_url = llm_base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.llm_model = llm_model or os.getenv("OPENAI_MODEL") or "gpt-4o"
        
        # 使用类变量作为全局缓存（跨实例共享）
        if not hasattr(PlannerService, '_locked_workflows'):
            PlannerService._locked_workflows: dict[str, LockedWorkflow] = {}
        if not hasattr(PlannerService, '_draft_cache'):
            PlannerService._draft_cache: dict[str, WorkflowDraft] = {}

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

        logger.debug("calling_llm", url=f"{self.llm_base_url}/chat/completions", model=self.llm_model)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.llm_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            
            if response.status_code != 200:
                logger.error("llm_api_error", status_code=response.status_code, response=response.text)
                response.raise_for_status()
                
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _normalize_draft(self, data: dict[str, Any]) -> dict[str, Any]:
        """规范化 draft 数据，处理各种 LLM 返回格式."""
        result: dict[str, Any] = {}
        
        # 处理嵌套结构
        source = data.get("workflow_draft", data)
        
        # 处理 base_info 嵌套
        if "base_info" in source:
            base = source["base_info"]
            result["name"] = base.get("name", "")
            result["description"] = base.get("description", "")
            result["version"] = base.get("version", "1.0.0")
        else:
            result["name"] = source.get("name", "")
            result["description"] = source.get("description", "")
            result["version"] = source.get("version", "1.0.0")
        
        # 4W1H 分析 - 支持 analysis_4w1h 和 analysis
        analysis = source.get("analysis_4w1h") or source.get("analysis", {})
        if analysis:
            result["what"] = analysis.get("what", "")
            result["why"] = analysis.get("why", "")
            result["who"] = analysis.get("who", "")
            result["when"] = analysis.get("when", "")
            result["how"] = analysis.get("how", "")
            result["analysis"] = analysis
        
        # 节点和边 - 支持 process_design 嵌套
        process_design = source.get("process_design", {})
        if process_design:
            result["nodes"] = process_design.get("nodes", [])
            result["edges"] = process_design.get("edges", [])
        else:
            result["nodes"] = source.get("nodes", [])
            result["edges"] = source.get("edges", [])
        
        # 输入输出 - 支持 input_output_definition 嵌套
        io_def = source.get("input_output_definition", {})
        if io_def:
            result["inputs"] = io_def.get("inputs", [])
            result["outputs"] = io_def.get("outputs", [])
        else:
            result["inputs"] = source.get("inputs", [])
            result["outputs"] = source.get("outputs", [])
        
        # 成本预估 - 支持 cost_estimation
        cost = source.get("cost_estimation") or source.get("cost_estimate", {})
        if isinstance(cost, dict):
            result["cost_estimate"] = {
                "estimated_tokens": cost.get("estimated_tokens", 1000),
                "estimated_cost_usd": cost.get("estimated_cost_usd", 0.01),
                "estimated_time_seconds": cost.get("estimated_time_seconds", 300),
            }
        
        # 风险处理 - 支持 risk_notes 嵌套字典
        risk_data = source.get("risk_notes", {})
        if isinstance(risk_data, dict):
            result["risk_level"] = risk_data.get("risk_level", "low")
            result["risk_notes"] = risk_data.get("risk_notes", [])
        elif isinstance(risk_data, list):
            result["risk_notes"] = risk_data
            result["risk_level"] = "low"
        else:
            result["risk_notes"] = []
            result["risk_level"] = "low"
        
        return result

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """解析 LLM 的 JSON 响应."""
        data = None
        
        # 尝试直接解析
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        if data is None and "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                try:
                    data = json.loads(response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # 尝试提取任意代码块
        if data is None and "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                try:
                    data = json.loads(response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        if data is None:
            raise ValueError(f"无法解析 JSON 响应: {response[:200]}...")
        
        # 规范化数据
        return self._normalize_draft(data)

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
        # 生成任务ID用于追踪
        import shortuuid
        task_id = f"plan_{shortuuid.uuid()}"
        logger.info("planning_workflow_start", task_id=task_id, goal=goal, context=context)

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
            logger.debug("calling_llm_start", task_id=task_id, model=self.llm_model, prompt_length=len(user_prompt))
            response = await self._call_llm(
                system_prompt=PLANNING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
            )
            logger.debug("calling_llm_end", task_id=task_id, response_length=len(response))

            # 解析响应
            logger.debug("parsing_response", task_id=task_id)
            draft_data = self._parse_json_response(response)
            logger.debug("response_parsed", task_id=task_id, keys=list(draft_data.keys()))
            
            # 生成 draft ID 并存储
            draft_id = f"draft_{shortuuid.uuid()}"
            draft_data["id"] = draft_id
            logger.debug("draft_created", task_id=task_id, draft_id=draft_id)
            
            draft = WorkflowDraft(**draft_data)

            # 如果 LLM 没有提供成本预估，补充一个
            if draft.cost_estimate is None:
                draft.cost_estimate = await self._estimate_cost(draft)
            
            # 缓存 draft 供 confirm 使用
            PlannerService._draft_cache[draft_id] = draft

            logger.info("planning_completed", task_id=task_id, workflow_name=draft.name, nodes_count=len(draft.nodes), draft_id=draft_id)

            return PlanningResult(
                success=True,
                draft=draft,
                raw_response=response,
            )

        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}"
            stack_trace = traceback.format_exc()
            logger.error("planning_failed", task_id=task_id, error=error_msg, stack_trace=stack_trace)
            return PlanningResult(
                success=False,
                error=error_msg,
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

        PlannerService._locked_workflows[workflow_id] = locked

        logger.info("workflow_locked", workflow_id=workflow_id, user_id=user_id)

        return locked

    async def get_locked(self, workflow_id: str) -> LockedWorkflow | None:
        """获取锁定的工作流."""
        return PlannerService._locked_workflows.get(workflow_id)

    async def unlock(
        self,
        workflow_id: str,
        reason: str,
        user_id: str | None = None,
    ) -> bool:
        """解锁工作流（用于修改）."""
        locked = PlannerService._locked_workflows.get(workflow_id)
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
        return list(PlannerService._locked_workflows.values())

    async def confirm(self, draft_id: str, user_id: str | None = None) -> LockedWorkflow:
        """确认并锁定工作流草案.
        
        Args:
            draft_id: 草案 ID
            user_id: 用户标识
            
        Returns:
            锁定的工作流
            
        Raises:
            ValueError: 如果 draft_id 不存在
        """
        draft = PlannerService._draft_cache.get(draft_id)
        if not draft:
            raise ValueError(f"Draft {draft_id} not found or expired")
        
        locked = await self.lock(draft, user_id)
        
        # 从缓存中移除已确认的 draft
        del PlannerService._draft_cache[draft_id]
        
        return locked

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
