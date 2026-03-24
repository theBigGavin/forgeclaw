# ForgeClaw

确定性 AI Agent 编排平台

> **核心理念**：LLM 负责规划，确定性引擎负责执行。

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 背景

现有 Agent 系统（如 OpenClaw）存在以下问题：
1. **流程不确定性**：依赖 LLM 实时决策，每次执行结果不同
2. **黑盒问题**：执行过程缺乏可见性和可控性
3. **记忆低效**：基于文本的记忆难以高效检索
4. **Skill 发现不确定**：LLM 倾向于"发明"而非使用已有 Skill

ForgeClaw 通过**规划-执行分离**解决这些问题。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     规划阶段 (Planning Phase)                     │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │ 用户目标 │───▶│ LLM Planner │───▶│ Workflow Definition     │  │
│  │ (目标)   │    │ (知识+推理)  │    │ (JSON/YAML 契约)        │  │
│  └─────────┘    └─────────────┘    └─────────────────────────┘  │
│                                           │                      │
│                                           ▼                      │
│                              ┌─────────────────────────┐         │
│                              │ 用户确认/修改            │         │
│                              │ (目标对齐 & 契约锁定)    │         │
│                              └─────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     执行阶段 (Execution Phase)                    │
│  ┌─────────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │ Workflow Engine │───▶│ Skill Nodes │───▶│  Output/Deliver │  │
│  │ (确定性执行)     │    │ (原子技能)   │    │ (可观测 & 可控)  │  │
│  └─────────────────┘    └─────────────┘    └─────────────────┘  │
│         │                      │                                │
│         ▼                      ▼                                │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ State Manager   │    │ Asset Generator │                     │
│  │ (结构化记忆)     │    │ (LLM创意生产)    │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## 核心特性

- ✅ **确定性执行**：同一输入，同一输出
- ✅ **流程可见**：全链路可视化
- ✅ **任意介入**：暂停、修改、恢复
- ✅ **契约锁定**：用户确认后不再改变
- ✅ **成本可控**：执行前预估 Token 消耗
- ✅ **结构化记忆**：替代 Markdown，支持向量检索
- ✅ **定时任务**：上下文继承，结果回流
- ✅ **资产管理**：版本控制、溯源追踪

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/forgeclaw.git
cd forgeclaw

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

### 启动服务

```bash
# 使用启动脚本
./start.sh

# 或手动启动
uvicorn forgeclaw.api.main:app --reload
```

### API 文档

启动后访问：http://localhost:8000/docs

### 示例：创建并执行工作流

```bash
# 创建工作流
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/simple_workflow.json

# 执行工作流
curl -X POST http://localhost:8000/api/v1/executions/my_workflow \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"text": "Hello World"}}'
```

## 项目结构

```
forgeclaw/
├── src/forgeclaw/
│   ├── api/              # REST API (FastAPI)
│   ├── assets/           # 资产管理
│   ├── engine/           # 工作流执行引擎
│   ├── memory/           # 结构化记忆
│   ├── models/           # 数据模型
│   ├── planner/          # LLM 规划服务
│   ├── scheduler/        # 定时任务
│   └── skills/           # Skill 系统
├── examples/             # 示例工作流
├── tests/                # 测试
└── docs/                 # 文档
```

## 开发阶段

### Phase 1: 核心引擎 ✅
- ✅ 工作流定义 Schema（YAML/JSON）
- ✅ 确定性执行引擎（状态机驱动）
- ✅ Skill Registry（注册、版本管理）
- ✅ 基础 Skill（code, template, http）
- ✅ REST API（FastAPI）
- ✅ 状态持久化（支持暂停/恢复）

### Phase 2: 规划与契约 ✅
- ✅ Planner Service（LLM 规划）
- ✅ 4W1H 分析框架
- ✅ 工作流草案生成
- ✅ 成本预估（Token/成本/时间）
- ✅ 风险提示
- ✅ 契约锁定机制
- ✅ 草案修改反馈

### Phase 3: 增强功能 ✅
- ✅ 结构化记忆系统（替代 Markdown）
- ✅ 关系图谱（工作流/Skill/资产关联）
- ✅ 语义检索（向量相似度）
- ✅ 上下文快照
- ✅ 定时任务服务（Cron/Interval/Event）
- ✅ 上下文继承策略
- ✅ 结果回流到记忆
- ✅ 资产管理（版本控制、溯源、共享）

### Phase 4: UI 与体验 🚧
- [ ] Web UI（React）
- [ ] 工作流可视化编辑器
- [ ] 执行监控面板
- [ ] 对话界面

## 核心概念

### 规划-执行分离

**规划阶段**：
```python
# LLM 根据用户目标生成草案
result = await planner.plan(
    goal="分析 Tesla 和 BYD 的竞争优势",
    context={"industry": "automotive"}
)
draft = result.draft  # 工作流草案

# 用户确认后锁定
locked = await planner.lock(draft, user_id="user_123")
```

**执行阶段**：
```python
# 确定性引擎执行，无 LLM 参与
result = await executor.execute(workflow_def, inputs)
```

### 结构化记忆

```python
# 记录工作流执行
await memory.record_workflow_execution(
    workflow_id="wf_analysis",
    execution_id="exec_001",
    status="completed",
    inputs={"topic": "AI"},
    outputs={"report": "..."},
)

# 构建上下文快照
snapshot = await memory.build_context(
    project_id="proj_001",
    semantic_query="AI trends",
)
```

### 定时任务

```python
from forgeclaw.scheduler.models import ScheduledTask, TriggerType, CronTrigger

# 创建定时任务
task = ScheduledTask(
    id="daily_report",
    name="每日报告",
    trigger_type=TriggerType.CRON,
    cron=CronTrigger(hour="9", minute="0"),  # 每天 9:00
    locked_workflow_id="wf_report",
    context_policy=ContextInheritancePolicy.RECENT,
)
```

### 资产管理

```python
from forgeclaw.assets.models import AssetType

# 存储资产
asset = await asset_manager.store(
    content=report_bytes,
    name="Report.pdf",
    asset_type=AssetType.DOCUMENT,
    created_by="wf_report",
    lineage=lineage,  # 生成链路
)

# 创建新版本
v2 = await asset_manager.create_version(asset.id, new_content, "Added charts")
```

## API 概览

| 类别 | 路径 | 说明 |
|------|------|------|
| **工作流** | `POST /api/v1/workflows` | 创建工作流 |
| | `GET /api/v1/workflows/{id}` | 获取工作流 |
| | `POST /api/v1/executions/{id}` | 执行工作流 |
| | `POST /api/v1/executions/{id}/pause` | 暂停执行 |
| **Skill** | `GET /api/v1/skills` | 列出 Skills |
| **规划** | `POST /api/v1/planner/plan` | LLM 规划 |
| | `POST /api/v1/planner/lock` | 锁定工作流 |
| | `GET /api/v1/planner/locked` | 列出锁定的工作流 |
| **记忆** | `POST /api/v1/memory/store` | 存储记忆 |
| | `POST /api/v1/memory/query` | 查询记忆 |
| | `POST /api/v1/memory/context` | 构建上下文快照 |
| **定时任务** | `POST /api/v1/scheduler` | 创建任务 |
| | `POST /api/v1/scheduler/{id}/trigger` | 手动触发 |
| | `GET /api/v1/scheduler/{id}/records` | 执行记录 |
| **资产** | `POST /api/v1/assets/upload` | 上传资产 |
| | `GET /api/v1/assets/{id}/content` | 获取内容 |
| | `POST /api/v1/assets/{id}/version` | 创建版本 |

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11+, FastAPI, Pydantic |
| **执行引擎** | 自研，状态机驱动，异步执行 |
| **存储** | 文件（MVP）→ PostgreSQL（生产） |
| **部署** | Docker, Docker Compose |
| **前端** | React（Phase 4） |

## 设计理念

### 确定性优先
- 默认严格确定，同一输入必然同一输出
- 不确定性只允许出现在规划阶段
- 例外需显式授权（如安全更新），并记录审计日志

### 成本可控
- 规划阶段预估 Token 消耗和成本
- 执行阶段硬性预算限制
- 超出预算时暂停等待用户决策

### 契约精神
- 工作流锁定后即为契约，执行阶段严格遵守
- 任何修改都需重新规划、确认、锁定
- 完整的审计日志

## 贡献指南

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

[MIT](LICENSE)

---

Made with ❤️ by the ForgeClaw Team
