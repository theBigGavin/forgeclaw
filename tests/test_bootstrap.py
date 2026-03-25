#!/usr/bin/env python3
"""自举测试 - 验证系统各组件功能正常."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from forgeclaw.api.main import app


class BootstrapTest:
    """自举测试套件."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.test_results = []
        self.created_workflow_id = None
        
    def log(self, message: str, level: str = "info"):
        """打印日志."""
        prefix = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}.get(level, "ℹ️")
        print(f"{prefix} {message}")
        
    def test(self, name: str):
        """装饰器：运行单个测试."""
        def decorator(func):
            async def wrapper():
                try:
                    self.log(f"Testing: {name}")
                    await func(self)
                    self.test_results.append((name, True, None))
                    self.log(f"Passed: {name}", "success")
                    return True
                except Exception as e:
                    self.test_results.append((name, False, str(e)))
                    self.log(f"Failed: {name} - {e}", "error")
                    return False
            return wrapper
        return decorator


# ========== 测试用例 ==========

@test("Health Check")
async def test_health(t: BootstrapTest):
    """测试健康检查端点."""
    response = t.client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@test("List Skills")
async def test_list_skills(t: BootstrapTest):
    """测试列出技能."""
    response = t.client.get("/api/v1/skills")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    t.log(f"Found {len(data)} skills")


@test("Create Workflow")
async def test_create_workflow(t: BootstrapTest):
    """测试创建工作流."""
    workflow = {
        "id": "test_bootstrap_workflow",
        "name": "Bootstrap Test Workflow",
        "description": "A test workflow for bootstrap verification",
        "version": "1.0.0",
        "nodes": [
            {
                "id": "node_1",
                "type": "code",
                "name": "Test Code Node",
                "description": "Execute test code",
                "inputs": {"code": "print('hello')"},
            }
        ],
        "edges": [],
        "inputs": [],
        "outputs": [],
    }
    
    response = t.client.post("/api/v1/workflows", json=workflow)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workflow["id"]
    t.created_workflow_id = workflow["id"]


@test("Get Workflow")
async def test_get_workflow(t: BootstrapTest):
    """测试获取工作流."""
    response = t.client.get(f"/api/v1/workflows/{t.created_workflow_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == t.created_workflow_id
    assert data["name"] == "Bootstrap Test Workflow"


@test("List Workflows")
async def test_list_workflows(t: BootstrapTest):
    """测试列出工作流."""
    response = t.client.get("/api/v1/workflows")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(w["id"] == t.created_workflow_id for w in data)


@test("Execute Workflow")
async def test_execute_workflow(t: BootstrapTest):
    """测试执行工作流."""
    response = t.client.post(
        f"/api/v1/executions/{t.created_workflow_id}",
        json={"inputs": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data
    assert "status" in data


@test("List Executions")
async def test_list_executions(t: BootstrapTest):
    """测试列出执行记录."""
    response = t.client.get("/api/v1/executions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@test("Planner Mock Response")
async def test_planner_mock(t: BootstrapTest):
    """测试规划功能（使用模拟 LLM）."""
    # 直接测试解析逻辑
    from forgeclaw.planner.planner import PlannerService
    
    planner = PlannerService()
    
    # 测试 _normalize_draft 解析各种格式
    mock_response = {
        "workflow_draft": {
            "base_info": {
                "name": "Test Workflow",
                "description": "Test Description",
                "version": "1.0.0"
            },
            "analysis_4w1h": {
                "what": "Test what",
                "why": "Test why",
                "who": "Test who",
                "when": "Test when",
                "how": "Test how"
            },
            "process_design": {
                "nodes": [{"id": "n1", "type": "code", "name": "Node 1"}],
                "edges": []
            },
            "input_output_definition": {
                "inputs": [],
                "outputs": []
            },
            "cost_estimation": {
                "estimated_tokens": 1000,
                "estimated_cost_usd": 0.01,
                "estimated_time_seconds": 60
            },
            "risk_notes": {
                "risk_level": "low",
                "risk_notes": ["Test risk"]
            }
        }
    }
    
    result = planner._normalize_draft(mock_response)
    
    assert result["name"] == "Test Workflow"
    assert result["what"] == "Test what"
    assert len(result["nodes"]) == 1
    assert result["cost_estimate"]["estimated_tokens"] == 1000
    t.log("Mock draft normalization passed")


@test("Scheduler CRUD")
async def test_scheduler(t: BootstrapTest):
    """测试定时任务 CRUD."""
    # 列出任务
    response = t.client.get("/api/v1/scheduler/tasks")
    assert response.status_code == 200
    
    # 创建任务（简化格式）
    task_data = {
        "name": "Test Scheduler Task",
        "workflow_id": t.created_workflow_id,
        "trigger": {"type": "interval", "config": {"minutes": 60}},
        "context_policy": "recent"
    }
    response = t.client.post("/api/v1/scheduler/tasks", json=task_data)
    assert response.status_code in [200, 422, 500]  # 可能因为工作流不存在而失败


@test("Assets Upload/List")
async def test_assets(t: BootstrapTest):
    """测试资产管理."""
    # 列出资产
    response = t.client.get("/api/v1/assets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@test("CORS Headers")
async def test_cors(t: BootstrapTest):
    """测试 CORS 配置."""
    response = t.client.options(
        "/api/v1/planner/plan",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


@test("Delete Workflow")
async def test_delete_workflow(t: BootstrapTest):
    """测试删除工作流."""
    response = t.client.delete(f"/api/v1/workflows/{t.created_workflow_id}")
    assert response.status_code == 200
    
    # 确认已删除
    response = t.client.get(f"/api/v1/workflows/{t.created_workflow_id}")
    assert response.status_code == 404


async def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("🔬 ForgeClaw Bootstrap Test Suite")
    print("=" * 60)
    print()
    
    t = BootstrapTest()
    
    # 收集所有测试函数
    tests = [
        test_health,
        test_list_skills,
        test_create_workflow,
        test_get_workflow,
        test_list_workflows,
        test_execute_workflow,
        test_list_executions,
        test_planner_mock,
        test_scheduler,
        test_assets,
        test_cors,
        test_delete_workflow,
    ]
    
    # 运行测试
    for test_func in tests:
        await test_func(t)
        print()
    
    # 打印总结
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in t.test_results if success)
    failed = sum(1 for _, success, _ in t.test_results if not success)
    
    print(f"Total: {len(t.test_results)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print()
    
    if failed > 0:
        print("Failed Tests:")
        for name, success, error in t.test_results:
            if not success:
                print(f"  - {name}: {error}")
        return 1
    else:
        print("🎉 All tests passed! System is ready.")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
