"""定时任务模型."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    """触发器类型."""

    CRON = "cron"  # Cron 表达式
    INTERVAL = "interval"  # 固定间隔
    EVENT = "event"  # 事件触发
    ONCE = "once"  # 一次性任务


class ContextInheritancePolicy(str, Enum):
    """上下文继承策略."""

    NONE = "none"  # 不继承，全新开始
    RECENT = "recent"  # 继承最近 N 条记忆
    FILTERED = "filtered"  # 按条件过滤继承
    FULL = "full"  # 继承所有上下文


class CronTrigger(BaseModel):
    """Cron 触发器."""

    minute: str = Field(default="*", description="分钟 (0-59)")
    hour: str = Field(default="*", description="小时 (0-23)")
    day: str = Field(default="*", description="日期 (1-31)")
    month: str = Field(default="*", description="月份 (1-12)")
    day_of_week: str = Field(default="*", description="星期 (0-6, 0=周日)")

    def to_cron_string(self) -> str:
        """转换为 Cron 字符串."""
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.day_of_week}"


class IntervalTrigger(BaseModel):
    """间隔触发器."""

    seconds: int = Field(default=0, ge=0)
    minutes: int = Field(default=0, ge=0)
    hours: int = Field(default=0, ge=0)
    days: int = Field(default=0, ge=0)

    def total_seconds(self) -> int:
        """总秒数."""
        return self.seconds + self.minutes * 60 + self.hours * 3600 + self.days * 86400


class EventTrigger(BaseModel):
    """事件触发器."""

    event_type: str = Field(description="事件类型")
    event_filter: dict[str, Any] = Field(default_factory=dict, description="事件过滤条件")


class ScheduledTask(BaseModel):
    """定时任务定义."""

    id: str = Field(..., description="任务唯一标识")
    name: str = Field(..., description="任务名称")
    description: str = Field(default="", description="任务描述")

    # 触发条件
    trigger_type: TriggerType
    cron: CronTrigger | None = None
    interval: IntervalTrigger | None = None
    event: EventTrigger | None = None
    run_at: str | None = None  # 一次性任务的执行时间

    # 执行内容（引用锁定的工作流）
    locked_workflow_id: str = Field(..., description="锁定的工作流 ID")

    # 上下文继承
    context_policy: ContextInheritancePolicy = Field(
        default=ContextInheritancePolicy.RECENT
    )
    context_config: dict[str, Any] = Field(default_factory=dict)
    # 例如：{"max_memories": 10, "time_range": "7d"}

    # 执行配置
    max_retries: int = Field(default=3, ge=0)
    timeout_seconds: int = Field(default=300, ge=0)

    # 状态
    enabled: bool = Field(default=True)
    last_run_at: str | None = None
    last_run_status: str | None = None  # success / failed / timeout
    last_run_execution_id: str | None = None
    next_run_at: str | None = None

    # 元数据
    created_at: str = Field(..., description="创建时间")
    created_by: str | None = None
    updated_at: str | None = None


class TaskExecutionRecord(BaseModel):
    """任务执行记录."""

    id: str = Field(..., description="记录 ID")
    task_id: str = Field(..., description="任务 ID")

    # 执行信息
    execution_id: str = Field(..., description="工作流执行 ID")
    started_at: str = Field(..., description="开始时间")
    completed_at: str | None = None
    status: str = Field(..., description="状态: success/failed/timeout")
    error: str | None = None

    # 继承的上下文
    inherited_context: dict[str, Any] = Field(default_factory=dict)

    # 输出回流
    outputs: dict[str, Any] = Field(default_factory=dict)
