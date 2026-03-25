"""测试配置和 fixtures."""

import asyncio
import os
import sys
from pathlib import Path

# 确保 src 在路径中
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx
import pytest
from fastapi.testclient import TestClient

from forgeclaw.api.main import app


@pytest.fixture
def client():
    """同步测试客户端."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """异步测试客户端."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_workflow():
    """示例工作流数据."""
    return {
        "id": "test_workflow_001",
        "name": "Test Workflow",
        "description": "A test workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "id": "node_1",
                "type": "code",
                "name": "Code Node",
                "description": "Execute code",
                "inputs": {"code": "print('hello')"},
            }
        ],
        "edges": [],
        "inputs": [],
        "outputs": [],
    }


@pytest.fixture
def sample_planner_request():
    """示例规划请求."""
    return {
        "goal": "Fetch weather data and send email summary",
        "context": {"city": "Beijing"}
    }
