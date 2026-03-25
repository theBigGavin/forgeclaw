#!/bin/bash

# 自举测试运行脚本

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           ForgeClaw Bootstrap Test Suite                 ║"
echo "║         Self-checking system verification               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "📋 Test Categories:"
echo "   1. System Health      - API connectivity"
echo "   2. Skill Registry     - Available skills"
echo "   3. Workflow Engine    - CRUD operations"
echo "   4. Execution Engine   - Run workflows"
echo "   5. Planner Parser     - LLM response handling"
echo "   6. Scheduler          - Task management"
echo "   7. Assets             - File management"
echo "   8. CORS               - Frontend compatibility"
echo ""

# 运行测试
python3 tests/test_bootstrap.py

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "🚀 System ready for development!"
    echo ""
    echo "Next steps:"
    echo "   ./start.sh --web    # Start full stack"
else
    echo "⚠️  Some tests failed. Check output above."
fi

exit $exit_code
