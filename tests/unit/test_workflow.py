"""工作流模型测试."""

import pytest

from forgeclaw.models.workflow import (
    Edge,
    ErrorPolicy,
    Node,
    NodeType,
    RetryPolicy,
    WorkflowDefinition,
    WorkflowInput,
    WorkflowOutput,
)


class TestWorkflowDefinition:
    """工作流定义测试."""

    def test_create_simple_workflow(self):
        """测试创建简单工作流."""
        workflow = WorkflowDefinition(
            id="test_workflow",
            name="测试工作流",
            nodes=[
                Node(id="node1", type=NodeType.CODE, code="outputs['result'] = 'hello'"),
                Node(id="node2", type=NodeType.CODE, code="outputs['result'] = 'world'"),
            ],
            edges=[
                Edge(from_node="node1", to_node="node2"),
            ],
        )

        assert workflow.id == "test_workflow"
        assert len(workflow.nodes) == 2
        assert len(workflow.edges) == 1

    def test_get_start_nodes(self):
        """测试获取起始节点."""
        workflow = WorkflowDefinition(
            id="test",
            nodes=[
                Node(id="a", type=NodeType.CODE, code=""),
                Node(id="b", type=NodeType.CODE, code=""),
                Node(id="c", type=NodeType.CODE, code=""),
            ],
            edges=[
                Edge(from_node="a", to_node="b"),
                Edge(from_node="b", to_node="c"),
            ],
        )

        start_nodes = workflow.get_start_nodes()
        assert len(start_nodes) == 1
        assert start_nodes[0].id == "a"

    def test_get_next_nodes(self):
        """测试获取后续节点."""
        workflow = WorkflowDefinition(
            id="test",
            nodes=[
                Node(id="a", type=NodeType.CODE, code=""),
                Node(id="b", type=NodeType.CODE, code=""),
                Node(id="c", type=NodeType.CODE, code=""),
            ],
            edges=[
                Edge(from_node="a", to_node="b"),
                Edge(from_node="a", to_node="c", condition="${x} > 0"),
            ],
        )

        next_nodes = workflow.get_next_nodes("a")
        assert len(next_nodes) == 2
        assert next_nodes[0][0].id == "b"
        assert next_nodes[0][1] is None
        assert next_nodes[1][0].id == "c"
        assert next_nodes[1][1] == "${x} > 0"

    def test_invalid_edge_reference(self):
        """测试无效边引用应报错."""
        with pytest.raises(ValueError, match="边引用了不存在的节点"):
            WorkflowDefinition(
                id="test",
                nodes=[
                    Node(id="a", type=NodeType.CODE, code=""),
                ],
                edges=[
                    Edge(from_node="a", to_node="nonexistent"),
                ],
            )


class TestNode:
    """节点测试."""

    def test_skill_node_requires_skill_id(self):
        """测试 skill 节点需要 skill_id."""
        with pytest.raises(ValueError, match="skill 类型节点必须指定 skill_id"):
            Node(id="test", type=NodeType.SKILL)

    def test_code_node_requires_code(self):
        """测试 code 节点需要 code."""
        with pytest.raises(ValueError, match="code 类型节点必须指定 code"):
            Node(id="test", type=NodeType.CODE)

    def test_retry_policy(self):
        """测试重试策略."""
        policy = RetryPolicy(max_attempts=5, initial_delay=2.0)
        assert policy.max_attempts == 5
        assert policy.initial_delay == 2.0

    def test_error_policy(self):
        """测试错误策略."""
        policy = ErrorPolicy(on_error="skip")
        assert policy.on_error == "skip"


class TestEdge:
    """边测试."""

    def test_edge_creation(self):
        """测试边创建."""
        edge = Edge(from_node="a", to_node="b")
        assert edge.from_node == "a"
        assert edge.to_node == "b"
        assert edge.condition is None

    def test_edge_with_condition(self):
        """测试带条件的边."""
        edge = Edge(from_node="a", to_node="b", condition="${x} > 0")
        assert edge.condition == "${x} > 0"
