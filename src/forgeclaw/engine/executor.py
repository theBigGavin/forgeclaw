"""工作流执行引擎."""

import asyncio
import json
import re
from datetime import datetime
from typing import Any

import structlog

from forgeclaw.engine.state import ExecutionStateManager
from forgeclaw.models.execution import (
    ExecutionContext,
    ExecutionResult,
    ExecutionState,
    ExecutionStatus,
    NodeExecutionResult,
    NodeExecutionStatus,
)
from forgeclaw.models.workflow import Node, NodeType, WorkflowDefinition
from forgeclaw.skills.registry import SkillRegistry

logger = structlog.get_logger()


class WorkflowExecutor:
    """确定性工作流执行引擎.

    核心原则：
    1. 无 LLM 参与流程决策
    2. 状态可持久化，支持断点续传
    3. 任意节点可暂停/恢复/终止
    """

    def __init__(self, skill_registry: SkillRegistry | None = None):
        self.skill_registry = skill_registry or SkillRegistry()
        self.state_manager = ExecutionStateManager()
        self._running: dict[str, asyncio.Event] = {}  # 执行控制信号

    async def execute(
        self,
        workflow: WorkflowDefinition,
        inputs: dict[str, Any],
        execution_id: str | None = None,
    ) -> ExecutionResult:
        """执行工作流.

        Args:
            workflow: 工作流定义
            inputs: 工作流输入
            execution_id: 可选的执行ID（用于恢复）

        Returns:
            执行结果
        """
        execution_id = execution_id or self._generate_execution_id()

        # 初始化执行上下文
        context = ExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow.id,
            inputs=inputs,
            start_time=datetime.utcnow().isoformat(),
        )

        # 初始化执行状态
        state = ExecutionState(
            execution_id=execution_id,
            workflow_id=workflow.id,
            status=ExecutionStatus.PENDING,
            context=context,
            start_time=context.start_time,
        )

        # 查找起始节点
        start_nodes = workflow.get_start_nodes()
        if not start_nodes:
            raise ValueError("工作流没有起始节点")

        state.current_nodes = [n.id for n in start_nodes]
        state.status = ExecutionStatus.RUNNING

        # 创建控制信号
        self._running[execution_id] = asyncio.Event()
        self._running[execution_id].set()  # 默认运行状态

        try:
            await self._run_workflow(state, workflow)
        except asyncio.CancelledError:
            state.status = ExecutionStatus.TERMINATED
            logger.info("workflow_terminated", execution_id=execution_id)
        except Exception as e:
            state.status = ExecutionStatus.FAILED
            logger.error("workflow_failed", execution_id=execution_id, error=str(e))
        finally:
            state.end_time = datetime.utcnow().isoformat()
            await self.state_manager.save_state(state)
            self._running.pop(execution_id, None)

        return self._build_result(state, workflow)

    async def _run_workflow(self, state: ExecutionState, workflow: WorkflowDefinition) -> None:
        """运行工作流主循环."""
        while state.current_nodes:
            # 检查控制信号
            if execution_id := state.execution_id:
                if execution_id in self._running:
                    await self._running[execution_id].wait()

            # 检查是否被终止
            if state.status == ExecutionStatus.TERMINATED:
                break

            # 获取可执行节点（依赖已完成的）
            ready_nodes = self._get_ready_nodes(state, workflow)
            if not ready_nodes:
                # 检查是否有运行中的节点
                if not any(
                    r.status == NodeExecutionStatus.RUNNING
                    for r in state.node_states.values()
                ):
                    break  # 没有可执行的节点了
                await asyncio.sleep(0.1)
                continue

            # 并行执行就绪节点
            tasks = [
                self._execute_node(node, state, workflow)
                for node in ready_nodes
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            # 持久化状态
            await self.state_manager.save_state(state)

        # 标记完成
        if state.status == ExecutionStatus.RUNNING:
            state.status = ExecutionStatus.COMPLETED

    def _get_ready_nodes(
        self, state: ExecutionState, workflow: WorkflowDefinition
    ) -> list[Node]:
        """获取可执行的节点（依赖已完成）."""
        ready = []
        for node_id in state.current_nodes:
            if node_id in state.completed_nodes:
                continue
            if node_id in [n for n, r in state.node_states.items() if r.status == NodeExecutionStatus.RUNNING]:
                continue

            # 检查依赖是否完成
            deps = workflow.get_dependencies(node_id)
            if all(d.id in state.completed_nodes for d in deps):
                node = next((n for n in workflow.nodes if n.id == node_id), None)
                if node:
                    ready.append(node)

        return ready

    async def _execute_node(
        self, node: Node, state: ExecutionState, workflow: WorkflowDefinition
    ) -> None:
        """执行单个节点."""
        execution_id = state.execution_id

        # 初始化节点状态
        node_result = NodeExecutionResult(
            node_id=node.id,
            status=NodeExecutionStatus.RUNNING,
            start_time=datetime.utcnow().isoformat(),
        )
        state.node_states[node.id] = node_result

        try:
            # 解析输入
            inputs = self._resolve_inputs(node.inputs, state)
            logger.debug("node_inputs_resolved", node_id=node.id, inputs=inputs)

            # 根据节点类型执行
            match node.type:
                case NodeType.SKILL:
                    outputs = await self._execute_skill(node, inputs)
                case NodeType.CODE:
                    outputs = await self._execute_code(node, inputs)
                case NodeType.TEMPLATE:
                    outputs = await self._execute_template(node, inputs)
                case NodeType.DECISION:
                    outputs = await self._execute_decision(node, inputs)
                case _:
                    raise ValueError(f"不支持的节点类型: {node.type}")

            # 更新结果
            node_result.status = NodeExecutionStatus.COMPLETED
            node_result.outputs = outputs
            node_result.end_time = datetime.utcnow().isoformat()

            # 保存到上下文
            state.context.node_outputs[node.id] = outputs
            state.completed_nodes.append(node.id)
            state.current_nodes.remove(node.id)

            # 添加后续节点
            next_nodes = workflow.get_next_nodes(node.id)
            for next_node, condition in next_nodes:
                if self._evaluate_condition(condition, state):
                    if next_node.id not in state.completed_nodes:
                        state.current_nodes.append(next_node.id)

            logger.info("node_completed", node_id=node.id, execution_id=execution_id)

        except Exception as e:
            node_result.status = NodeExecutionStatus.FAILED
            node_result.error = str(e)
            node_result.end_time = datetime.utcnow().isoformat()

            # 错误处理
            error_policy = node.error_policy or workflow.default_error_policy
            if error_policy.on_error == "pause":
                state.status = ExecutionStatus.PAUSED
                logger.warning("node_paused", node_id=node.id, error=str(e))
            elif error_policy.on_error == "skip":
                state.completed_nodes.append(node.id)
                state.current_nodes.remove(node.id)
                logger.warning("node_skipped", node_id=node.id, error=str(e))
            else:
                state.status = ExecutionStatus.FAILED
                logger.error("node_failed", node_id=node.id, error=str(e))

    def _resolve_inputs(
        self, inputs: dict[str, Any], state: ExecutionState
    ) -> dict[str, Any]:
        """解析输入中的变量引用."""
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_value(value, state)
            else:
                resolved[key] = value
        return resolved

    def _resolve_value(self, value: str, state: ExecutionState) -> Any:
        """解析单个值中的变量引用.

        支持格式：
        - ${inputs.xxx} - 工作流输入
        - ${node_id.output_name} - 节点输出
        - ${variables.xxx} - 变量
        """
        pattern = r"\$\{([^}]+)\}"

        def replace(match: re.Match) -> str:
            path = match.group(1)
            parts = path.split(".")

            if parts[0] == "inputs":
                return str(state.context.inputs.get(parts[1], ""))
            elif parts[0] == "variables":
                return str(state.context.variables.get(parts[1], ""))
            else:
                # node_id.output_name
                node_outputs = state.context.node_outputs.get(parts[0], {})
                return str(node_outputs.get(parts[1], ""))

        if re.match(r"^\$\{[^}]+\}$", value):
            # 纯变量，返回原始类型
            path = value[2:-1]
            parts = path.split(".")

            if parts[0] == "inputs":
                return state.context.inputs.get(parts[1])
            elif parts[0] == "variables":
                return state.context.variables.get(parts[1])
            else:
                node_outputs = state.context.node_outputs.get(parts[0], {})
                return node_outputs.get(parts[1])

        # 字符串插值
        return re.sub(pattern, replace, value)

    def _evaluate_condition(self, condition: str | None, state: ExecutionState) -> bool:
        """评估条件表达式."""
        if condition is None:
            return True

        # 简单表达式评估（可以扩展）
        # 支持: ${var} == "value", ${var} > 10, ${var} == true
        try:
            # 解析变量
            resolved_condition = self._resolve_value(f"${{{condition}}}", state)
            if isinstance(resolved_condition, bool):
                return resolved_condition

            # 默认字符串比较
            return str(resolved_condition).lower() == "true"
        except Exception:
            return False

    async def _execute_skill(
        self, node: Node, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """执行 Skill."""
        if not node.skill_id:
            raise ValueError("skill 节点未指定 skill_id")

        skill = self.skill_registry.get(node.skill_id, node.skill_version)
        return await skill.execute(inputs)

    async def _execute_code(
        self, node: Node, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """执行代码节点."""
        if not node.code:
            raise ValueError("code 节点未指定 code")

        # 创建安全的执行环境
        namespace = {"inputs": inputs, "outputs": {}}
        exec(node.code, {"__builtins__": {}}, namespace)
        return namespace.get("outputs", {})

    async def _execute_template(
        self, node: Node, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """执行模板节点."""
        from jinja2 import Template

        if not node.template:
            raise ValueError("template 节点未指定 template")

        template = Template(node.template)
        result = template.render(**inputs)
        return {"result": result}

    async def _execute_decision(
        self, node: Node, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """执行决策节点."""
        # 决策节点本身不产出数据，只是流程控制
        # 实际的决策在 _evaluate_condition 中处理
        return {"passed": True}

    # 控制方法

    async def pause(self, execution_id: str) -> None:
        """暂停执行."""
        if execution_id in self._running:
            self._running[execution_id].clear()
            logger.info("execution_paused", execution_id=execution_id)

    async def resume(self, execution_id: str) -> None:
        """恢复执行."""
        if execution_id in self._running:
            self._running[execution_id].set()
            logger.info("execution_resumed", execution_id=execution_id)

    async def terminate(self, execution_id: str) -> None:
        """终止执行."""
        state = await self.state_manager.load_state(execution_id)
        if state:
            state.status = ExecutionStatus.TERMINATED
            await self.state_manager.save_state(state)

        if execution_id in self._running:
            self._running[execution_id].set()  # 唤醒以终止
        logger.info("execution_terminated", execution_id=execution_id)

    # 辅助方法

    def _generate_execution_id(self) -> str:
        """生成执行ID."""
        import shortuuid
        return f"exec_{shortuuid.uuid()}"

    def _build_result(
        self, state: ExecutionState, workflow: WorkflowDefinition
    ) -> ExecutionResult:
        """构建执行结果."""
        # 解析输出
        outputs = {}
        for output in workflow.outputs:
            value = self._resolve_value(output.source, state)
            outputs[output.name] = value

        return ExecutionResult(
            execution_id=state.execution_id,
            status=state.status,
            outputs=outputs,
            error=next(
                (r.error for r in state.node_states.values() if r.error),
                None,
            ),
            node_results=dict(state.node_states),
            start_time=state.start_time,
            end_time=state.end_time,
            tokens_used=state.tokens_used,
            estimated_cost=state.estimated_cost,
        )
