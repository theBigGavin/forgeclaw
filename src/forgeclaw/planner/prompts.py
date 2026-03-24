"""规划服务提示词模板."""

PLANNING_SYSTEM_PROMPT = """你是一个专业的工作流规划师，擅长将用户目标转化为确定性的工作流定义。

你的任务：
1. 分析用户目标，使用 4W1H 方法梳理需求
2. 盘点可用的 Skill 资产
3. 设计合理的工作流流程
4. 预估执行成本

原则：
- 确定性优先：流程一旦确定，执行阶段不再改变
- Skill 优先：优先使用已存在的 Skill，避免重新发明
- 成本可控：提供明确的 Token 消耗预估
- 风险透明：明确指出潜在风险

输出格式必须是合法的 JSON，符合 WorkflowDraft Schema。
"""

PLANNING_USER_PROMPT_TEMPLATE = """请为以下目标设计工作流：

## 用户目标
{goal}

## 上下文信息
{context}

## 可用 Skill 资产
{skills}

## 输出要求

请生成 WorkflowDraft JSON，包含：

1. **基础信息**：name, description, version

2. **4W1H 分析**：
   - what: 要做什么
   - why: 为什么做  
   - who: 涉及哪些 Skill
   - when: 执行时机
   - how: 如何执行

3. **流程设计**：
   - nodes: 节点列表，每个节点包含 id, type, name, description, skill_id, inputs, temperature
   - edges: 连接关系，from → to
   
4. **输入输出定义**：
   - inputs: 工作流需要的输入参数
   - outputs: 工作流的输出

5. **成本预估**：
   - estimated_tokens: 预估总 Token 数
   - estimated_cost_usd: 预估成本
   - estimated_time_seconds: 预估执行时间
   - breakdown: 各节点成本明细

6. **风险提示**：
   - risk_level: low/medium/high
   - risk_notes: 风险说明列表

## 节点类型说明

- **skill**: 调用已注册的 Skill，需要指定 skill_id 和 skill_version
- **code**: 执行 Python 代码，用于数据转换
- **template**: 使用 Jinja2 模板渲染文本
- **decision**: 条件分支，需要指定 condition

## 变量引用语法

在 inputs 中可以使用以下变量引用：
- `${{inputs.xxx}}`: 引用工作流输入
- `${{node_id.output_name}}`: 引用其他节点的输出

## 示例节点

```json
{{
  "id": "search",
  "type": "skill",
  "name": "网页搜索",
  "description": "搜索相关信息",
  "skill_id": "web_search",
  "skill_version": "1.0.0",
  "inputs": {{
    "query": "${{inputs.topic}}"
  }},
  "temperature": 0.3
}}
```

请只输出 JSON，不要输出其他内容。
"""

MODIFICATION_SYSTEM_PROMPT = """你是一个工作流修改助手，根据用户反馈修改工作流草案。

修改原则：
1. 保持原有结构稳定，只修改用户明确指出的部分
2. 保留用户认可的部分
3. 修改后重新计算成本预估
4. 如果用户要求不可行，说明原因并提供替代方案

输出格式必须是合法的 JSON，符合 WorkflowDraft Schema。
"""

MODIFICATION_USER_PROMPT_TEMPLATE = """请根据用户反馈修改工作流草案。

## 当前工作流草案
{current_draft}

## 用户反馈
Action: {action}
Feedback: {feedback_text}

## 具体修改要求
{modifications}

## 可用 Skill 资产
{skills}

请生成修改后的 WorkflowDraft JSON，保持原有格式，应用用户的修改意见。
如果某些修改不可行，请在 risk_notes 中说明。

只输出 JSON，不要输出其他内容。
"""

COST_ESTIMATION_PROMPT = """请为以下工作流进行成本预估。

工作流：
{workflow}

可用 Skill：
{skills}

请估算：
1. 每个节点的 Token 消耗（输入+输出）
2. 每个节点的执行时间
3. 总成本和总时间

输出 JSON 格式：
{{
  "estimated_tokens": 1234,
  "estimated_cost_usd": 0.05,
  "estimated_time_seconds": 30,
  "breakdown": [
    {{
      "node_id": "xxx",
      "estimated_tokens": 100,
      "estimated_cost_usd": 0.01,
      "estimated_time_seconds": 5
    }}
  ]
}}
"""

RISK_ASSESSMENT_PROMPT = """请评估以下工作流的风险等级。

工作流：
{workflow}

请从以下维度评估：
1. **确定性风险**：是否有不确定的执行路径
2. **成本风险**：预估成本是否可能大幅超支
3. **安全风险**：是否涉及敏感操作（如发送数据到外部）
4. **依赖风险**：Skill 是否稳定可靠

输出 JSON 格式：
{{
  "risk_level": "low|medium|high",
  "risk_notes": [
    "风险1描述",
    "风险2描述"
  ],
  "mitigations": [
    "缓解措施1",
    "缓解措施2"
  ]
}}
"""
