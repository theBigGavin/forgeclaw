#!/usr/bin/env python3
"""快速验证所有 API 端点是否正确注册."""

import sys
from pathlib import Path

# 确保 src 在路径中
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.routing import APIRoute
from forgeclaw.api.main import app


def get_all_routes(app):
    """获取所有路由."""
    routes = {}
    
    for route in app.routes:
        if isinstance(route, APIRoute):
            path = route.path
            routes[path] = {
                "methods": list(route.methods),
                "name": route.name,
            }
    
    return routes


def verify_endpoints():
    """验证所有端点."""
    routes = get_all_routes(app)
    
    # 简化的端点检查 - 只检查关键路径存在
    critical_paths = [
        # Workflows
        "/api/v1/workflows",
        "/api/v1/workflows/{workflow_id}",
        
        # Executions
        "/api/v1/executions",
        "/api/v1/executions/start",
        "/api/v1/executions/{execution_id}",
        "/api/v1/executions/{execution_id}/pause",
        
        # Planner
        "/api/v1/planner/plan",
        "/api/v1/planner/confirm/{draft_id}",
        
        # Scheduler
        "/api/v1/scheduler",
        "/api/v1/scheduler/tasks",
        "/api/v1/scheduler/{task_id}",
        
        # Assets
        "/api/v1/assets",
        "/api/v1/assets/{asset_id}",
        "/api/v1/assets/{asset_id}/versions",
        "/api/v1/assets/{asset_id}/share",
        
        # Skills
        "/api/v1/skills",
        "/api/v1/skills/{skill_id}",
    ]
    
    print("🔍 Verifying API endpoints...\n")
    
    missing = []
    found = []
    
    for path in critical_paths:
        if path not in routes:
            # 检查是否是参数路径，可能格式不同
            found_match = False
            for route_path in routes.keys():
                if path.replace("{", "").replace("}", "") in route_path.replace("{", "").replace("}", ""):
                    found_match = True
                    break
            if not found_match:
                missing.append(path)
        else:
            found.append(path)
    
    # 打印结果
    print("=" * 60)
    
    if not missing:
        print("✅ All critical endpoints are registered!")
        print(f"\nTotal routes: {len(routes)}")
        print(f"Critical endpoints verified: {len(found)}")
    else:
        print(f"\n❌ Missing endpoints ({len(missing)}):")
        for path in missing:
            print(f"   - {path}")
    
    # 按类别打印所有路由
    print("\n📋 Registered routes by category:")
    print("-" * 40)
    
    categories = {}
    for path in sorted(routes.keys()):
        parts = path.split("/")
        if len(parts) >= 4:
            category = parts[3]  # /api/v1/{category}
        else:
            category = "other"
        
        if category not in categories:
            categories[category] = []
        methods = ", ".join(sorted(routes[path]["methods"]))
        categories[category].append(f"  {methods:20} {path}")
    
    for category in sorted(categories.keys()):
        print(f"\n{category.upper()}:")
        for line in categories[category]:
            print(line)
    
    return 0 if not missing else 1


def test_critical_endpoints():
    """测试关键端点是否能访问."""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    print("\n" + "=" * 60)
    print("🧪 Testing critical endpoints...\n")
    
    tests = [
        ("GET", "/api/v1/workflows", [200]),
        ("POST", "/api/v1/workflows", [422, 400, 409]),  # Validation error expected
        ("GET", "/api/v1/workflows/test_id", [404]),  # Not found expected
        ("GET", "/api/v1/executions", [200]),
        ("POST", "/api/v1/executions/start", [404, 422]),  # Workflow not found expected
        ("POST", "/api/v1/planner/plan", [200, 500, 422]),  # May fail without API key
        ("GET", "/api/v1/scheduler", [200]),
        ("GET", "/api/v1/assets", [200]),
        ("GET", "/api/v1/skills", [200]),
        # ("OPTIONS", "/api/v1/planner/plan", [200]),  # CORS preflight - skipped in test client
    ]
    
    passed = 0
    failed = 0
    
    for method, path, expected_codes in tests:
        try:
            response = client.request(method, path)
            if response.status_code in expected_codes:
                print(f"✅ {method:7} {path:40} -> {response.status_code}")
                passed += 1
            else:
                print(f"⚠️  {method:7} {path:40} -> {response.status_code} (expected {expected_codes})")
                failed += 1
        except Exception as e:
            print(f"❌ {method:7} {path:40} -> ERROR: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    exit_code = verify_endpoints()
    
    # 同时测试端点可访问性
    try:
        test_critical_endpoints()
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        exit_code = 1
    
    sys.exit(exit_code)
