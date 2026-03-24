"""执行引擎测试."""

import pytest

from forgeclaw.engine.executor import WorkflowExecutor
from forgeclaw.models.execution import ExecutionStatus
from forgeclaw.models.workflow import (
    Edge,
    Node,
    NodeType,
    WorkflowDefinition,
    WorkflowInput,
    WorkflowOutput,
)


class TestWorkflowExecutor:
    """工作流执行器测试."""

    @pytest.fixture
    def executor(self):
        return WorkflowExecutor()

    async def test_execute_simple_linear_workflow(self, executor):
        """测试执行简单线性工作流."""
        workflow = WorkflowDefinition(
            id="linear_test",
            name="线性测试",
            inputs=[
                WorkflowInput(name="value", type="integer"),
            ],
            outputs=[
                WorkflowOutput(name="result", type="integer", source="${double.result}"),
            ],
            nodes=[
                Node(
                    id="input",
                    type=NodeType.CODE,
                    code="outputs['value'] = inputs['value']",
                ),
                Node(
                    id="double",
                    type=NodeType.CODE,
                    code="outputs['result'] = inputs['value'] * 2",
                    inputs={"value": "${input.value}"},
                ),
            ],
            edges=[
                Edge(from_node="input", to_node="double"),
            ],
        )

        result = await executor.execute(workflow, {"value": 5})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs["result"] == 10

    async def test_execute_with_template(self, executor):
        """测试执行带模板的工作流."""
        workflow = WorkflowDefinition(
            id="template_test",
            name="模板测试",
            inputs=[
                WorkflowInput(name="name", type="string"),
            ],
            outputs=[
                WorkflowOutput(name="greeting", type="string", source="${greet.result}"),
            ],
            nodes=[
                Node(
                    id="greet",
                    type=NodeType.TEMPLATE,
                    template="Hello, {{ name }}!",
                    inputs={"name": "${inputs.name}"},
                ),
            ],
        )

        result = await executor.execute(workflow, {"name": "World"})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs["greeting"] == "Hello, World!"

    async def test_execute_parallel_nodes(self, executor):
        """测试并行节点执行."""
        workflow = WorkflowDefinition(
            id="parallel_test",
            name="并行测试",
            outputs=[
                WorkflowOutput(name="a", type="string", source="${node_a.result}"),
                WorkflowOutput(name="b", type="string", source="${node_b.result}"),
            ],
            nodes=[
                Node(
                    id="node_a",
                    type=NodeType.CODE,
                    code="outputs['result'] = 'A'",
                ),
                Node(
                    id="node_b",
                    type=NodeType.CODE,
                    code="outputs['result'] = 'B'",
                ),
            ],
        )

        result = await executor.execute(workflow, {})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs["a"] == "A"
        assert result.outputs["b"] == "B"

    async def test_execute_with_condition(self, executor):
        """测试条件分支."""
        workflow = WorkflowDefinition(
            id="condition_test",
            name="条件测试",
            inputs=[
                WorkflowInput(name="score", type="integer"),
            ],
            outputs=[
                WorkflowOutput(name="result", type="string", source="${final.result}"),
            ],
            nodes=[
                Node(
                    id="check",
                    type=NodeType.CODE,
                    code="outputs['passed'] = inputs['score'] >= 60",
                    inputs={"score": "${inputs.score}"},
                ),
                Node(
                    id="pass",
                    type=NodeType.CODE,
                    code="outputs['result'] = 'Passed'",
                ),
                Node(
                    id="fail",
                    type=NodeType.CODE,
                    code="outputs['result'] = 'Failed'",
                ),
            ],
            edges=[
                Edge(from_node="check", to_node="pass"),
                Edge(from_node="check", to_node="fail"),
            ],
        )

        # 测试通过
        result = await executor.execute(workflow, {"score": 80})
        assert result.status == ExecutionStatus.COMPLETED

    async def test_error_handling(self, executor):
        """测试错误处理."""
        workflow = WorkflowDefinition(
            id="error_test",
            name="错误测试",
            nodes=[
                Node(
                    id="error_node",
                    type=NodeType.CODE,
                    code="raise ValueError('测试错误')",
                    error_policy={"on_error": "fail"},
                ),
            ],
        )

        result = await executor.execute(workflow, {})

        assert result.status == ExecutionStatus.FAILED
        assert "测试错误" in result.error
