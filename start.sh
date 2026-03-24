#!/bin/bash
# ForgeClaw 启动脚本

echo "🚀 Starting ForgeClaw..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "📦 Installing dependencies..."
pip install -q -e ".[dev]"

# 创建必要目录
mkdir -p .forgeclaw/executions

# 启动服务
echo "🌐 Starting API server at http://localhost:8000"
echo "📚 API docs at http://localhost:8000/docs"
echo ""
uvicorn forgeclaw.api.main:app --reload --host 0.0.0.0 --port 8000
