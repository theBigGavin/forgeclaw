#!/bin/bash

# ForgeClaw API 测试运行脚本

set -e

echo "╔════════════════════════════════════╗"
echo "║     ForgeClaw API Test Suite       ║"
echo "╚════════════════════════════════════╝"
echo ""

# 检查虚拟环境
if [ -f ".venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# 确保在正确的目录
cd "$(dirname "$0")/.."

# 安装测试依赖（如果需要）
echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio httpx -q

# 运行测试
echo ""
echo "🧪 Running API tests..."
echo ""

python -m pytest tests/test_api_integration.py -v --tb=short 2>&1 | tee tests/test_output.log

EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Check tests/test_output.log for details."
    echo ""
    echo "Failed tests summary:"
    grep -E "(FAILED|ERROR)" tests/test_output.log | head -20
fi

exit $EXIT_CODE
