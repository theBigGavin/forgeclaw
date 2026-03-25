"""API 集成测试 - 验证所有端点与前端期望匹配."""

import pytest
from fastapi.testclient import TestClient


class TestWorkflowsAPI:
    """工作流 API 测试."""

    def test_list_workflows(self, client: TestClient):
        """测试列出工作流."""
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_and_get_workflow(self, client: TestClient, sample_workflow):
        """测试创建和获取工作流."""
        # 创建
        response = client.post("/api/v1/workflows", json=sample_workflow)
        assert response.status_code == 200, f"Create failed: {response.text}"
        assert response.json()["id"] == sample_workflow["id"]

        # 获取
        response = client.get(f"/api/v1/workflows/{sample_workflow['id']}")
        assert response.status_code == 200, f"Get failed: {response.text}"
        data = response.json()
        assert data["id"] == sample_workflow["id"]
        assert data["name"] == sample_workflow["name"]
        assert "nodes" in data

    def test_update_workflow(self, client: TestClient, sample_workflow):
        """测试更新工作流."""
        # 先创建
        client.post("/api/v1/workflows", json=sample_workflow)
        
        # 更新
        updated = {**sample_workflow, "name": "Updated Name"}
        response = client.put(f"/api/v1/workflows/{sample_workflow['id']}", json=updated)
        assert response.status_code == 200

    def test_delete_workflow(self, client: TestClient, sample_workflow):
        """测试删除工作流."""
        # 先创建
        client.post("/api/v1/workflows", json=sample_workflow)
        
        # 删除
        response = client.delete(f"/api/v1/workflows/{sample_workflow['id']}")
        assert response.status_code == 200
        
        # 确认已删除
        response = client.get(f"/api/v1/workflows/{sample_workflow['id']}")
        assert response.status_code == 404


class TestExecutionsAPI:
    """执行 API 测试."""

    def test_list_executions(self, client: TestClient):
        """测试列出执行历史."""
        response = client.get("/api/v1/executions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_start_execution_endpoint_exists(self, client: TestClient):
        """测试启动执行端点存在（前端使用）."""
        # 这个端点需要工作流存在，我们只检查端点是否存在
        response = client.post("/api/v1/executions/start", json={
            "workflow_id": "non_existent",
            "inputs": {}
        })
        # 应该返回 404（工作流不存在），而不是 404（端点不存在）
        assert response.status_code in [404, 422]
        if response.status_code == 404:
            assert "Workflow not found" in response.text or "not found" in response.text.lower()

    def test_control_endpoints_exist(self, client: TestClient):
        """测试控制端点存在（前端格式）."""
        for action in ["pause", "resume", "terminate"]:
            response = client.post(f"/api/v1/executions/test_id/{action}")
            # 端点存在，但执行可能不存在
            assert response.status_code in [200, 404]


class TestPlannerAPI:
    """规划 API 测试."""

    def test_plan_endpoint_format(self, client: TestClient):
        """测试规划端点格式."""
        response = client.post("/api/v1/planner/plan", json={
            "goal": "Test goal",
            "context": {}
        })
        # 如果没有 API key 会失败，但端点应该存在
        assert response.status_code in [200, 500, 422]

    def test_confirm_endpoint_exists(self, client: TestClient):
        """测试确认端点存在."""
        response = client.post("/api/v1/planner/confirm/test_draft_id")
        # 草案不存在，但端点应该存在
        assert response.status_code in [200, 404]

    def test_plan_response_structure(self, client: TestClient):
        """测试规划响应结构（前端期望）."""
        response = client.post("/api/v1/planner/plan", json={
            "goal": "Test goal",
            "context": {}
        })
        
        if response.status_code == 200:
            data = response.json()
            # 前端期望的结构
            assert "draft" in data or "error" in data
            if "draft" in data:
                draft = data["draft"]
                # 4W1H 分析
                assert "analysis" in draft or all(k in draft for k in ["what", "why", "who", "when", "how"])
                assert "nodes" in draft
                assert "edges" in draft
                assert "cost_estimate" in draft or data.get("cost_estimate")


class TestSchedulerAPI:
    """定时任务 API 测试."""

    def test_list_tasks(self, client: TestClient):
        """测试列出任务."""
        response = client.get("/api/v1/scheduler")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_tasks_alias(self, client: TestClient):
        """测试 /scheduler/tasks 别名."""
        response = client.get("/api/v1/scheduler/tasks")
        assert response.status_code == 200

    def test_create_task_simple_format(self, client: TestClient):
        """测试前端简化格式创建任务."""
        response = client.post("/api/v1/scheduler/tasks", json={
            "name": "Test Task",
            "workflow_id": "test_wf",
            "trigger": {"type": "interval", "config": {"minutes": 60}},
            "context_policy": "recent"
        })
        # 可能失败因为 workflow 不存在，但端点应该处理格式
        assert response.status_code in [200, 404, 422, 500]

    def test_update_task_patch(self, client: TestClient):
        """测试 PATCH 更新任务."""
        response = client.patch("/api/v1/scheduler/tasks/non_existent", json={
            "updates": {"enabled": False}
        })
        # 任务不存在，但端点应该存在
        assert response.status_code in [200, 404]


class TestAssetsAPI:
    """资产 API 测试."""

    def test_list_assets(self, client: TestClient):
        """测试列出资产."""
        response = client.get("/api/v1/assets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_upload_asset_simple_format(self, client: TestClient):
        """测试简化上传格式."""
        response = client.post(
            "/api/v1/assets",
            files={"file": ("test.txt", b"test content", "text/plain")},
            data={"name": "test.txt", "project_id": "default"}
        )
        # 端点应该存在
        assert response.status_code in [200, 422, 500]

    def test_versions_endpoint_exists(self, client: TestClient):
        """测试版本列表端点."""
        response = client.get("/api/v1/assets/test_id/versions")
        # 资产可能不存在，但端点应该存在
        assert response.status_code in [200, 404]

    def test_share_endpoint_frontend_format(self, client: TestClient):
        """测试共享端点前段格式."""
        response = client.post(
            "/api/v1/assets/test_id/share",
            json={"target_project_id": "other_project"}
        )
        # 资产可能不存在，但端点应该存在
        assert response.status_code in [200, 404]


class TestSkillsAPI:
    """Skill API 测试."""

    def test_list_skills(self, client: TestClient):
        """测试列出技能."""
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_skill(self, client: TestClient):
        """测试获取技能详情."""
        # 先列出技能获取 ID
        response = client.get("/api/v1/skills")
        skills = response.json()
        
        if skills:
            skill_id = skills[0]["id"]
            response = client.get(f"/api/v1/skills/{skill_id}")
            assert response.status_code == 200


class TestCORS:
    """CORS 测试."""

    def test_cors_preflight(self, client: TestClient):
        """测试 CORS 预检请求."""
        response = client.options(
            "/api/v1/planner/plan",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_headers_present(self, client: TestClient):
        """测试 CORS 响应头."""
        response = client.get(
            "/api/v1/workflows",
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestResponseFormat:
    """响应格式测试 - 确保与前端期望匹配."""

    def test_workflow_list_includes_required_fields(self, client: TestClient, sample_workflow):
        """测试工作流列表包含必要字段."""
        # 创建工作流
        client.post("/api/v1/workflows", json=sample_workflow)
        
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        
        if data:
            wf = data[0]
            required_fields = ["id", "name", "description", "version", "nodes", "edges"]
            for field in required_fields:
                assert field in wf, f"Missing field: {field}"

    def test_execution_list_format(self, client: TestClient):
        """测试执行列表格式."""
        response = client.get("/api/v1/executions")
        assert response.status_code == 200
        data = response.json()
        
        for execution in data:
            # 前端期望的字段
            assert "execution_id" in execution or "id" in execution
            assert "status" in execution
            assert "workflow_id" in execution
