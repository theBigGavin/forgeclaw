"""定时任务服务."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import structlog
from croniter import croniter

from forgeclaw.engine.executor import WorkflowExecutor
from forgeclaw.memory.memory_service import MemoryService
from forgeclaw.planner.planner import PlannerService
from forgeclaw.scheduler.models import (
    ContextInheritancePolicy,
    ScheduledTask,
    TaskExecutionRecord,
    TriggerType,
)

logger = structlog.get_logger()


class ScheduleService:
    """定时任务服务.

    解决 OpenClaw 定时任务的问题：
    - 与主服务共享上下文状态
    - 执行结果回流到记忆
    - 支持上下文继承策略
    """

    def __init__(
        self,
        planner: PlannerService | None = None,
        executor: WorkflowExecutor | None = None,
        memory: MemoryService | None = None,
        storage_path: str | None = None,
    ):
        self.planner = planner or PlannerService()
        self.executor = executor or WorkflowExecutor()
        self.memory = memory or MemoryService()

        self.storage_path = Path(storage_path or ".forgeclaw/scheduler")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 任务存储
        self._tasks: dict[str, ScheduledTask] = {}
        self._load_tasks()

        # 执行记录
        self._records: dict[str, list[TaskExecutionRecord]] = {}

        # 运行状态
        self._running = False
        self._task_handles: dict[str, asyncio.Task] = {}

    def _load_tasks(self) -> None:
        """加载任务."""
        tasks_file = self.storage_path / "tasks.json"
        if tasks_file.exists():
            with open(tasks_file) as f:
                data = json.load(f)
                for task_data in data:
                    task = ScheduledTask(**task_data)
                    self._tasks[task.id] = task

        logger.info("scheduler_tasks_loaded", count=len(self._tasks))

    def _save_tasks(self) -> None:
        """保存任务."""
        tasks_file = self.storage_path / "tasks.json"
        data = [task.model_dump(mode="json") for task in self._tasks.values()]
        with open(tasks_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    async def create_task(self, task: ScheduledTask) -> str:
        """创建定时任务."""
        self._tasks[task.id] = task
        self._save_tasks()

        # 如果服务正在运行，立即调度
        if self._running and task.enabled:
            self._schedule_task(task)

        logger.info("task_created", task_id=task.id, name=task.name)
        return task.id

    async def update_task(self, task_id: str, updates: dict[str, Any]) -> bool:
        """更新任务."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        # 更新字段
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.updated_at = datetime.utcnow().isoformat()
        self._save_tasks()

        # 重新调度
        if self._running:
            self._unschedule_task(task_id)
            if task.enabled:
                self._schedule_task(task)

        logger.info("task_updated", task_id=task_id)
        return True

    async def delete_task(self, task_id: str) -> bool:
        """删除任务."""
        if task_id not in self._tasks:
            return False

        # 取消调度
        if self._running:
            self._unschedule_task(task_id)

        del self._tasks[task_id]
        self._save_tasks()

        logger.info("task_deleted", task_id=task_id)
        return True

    async def get_task(self, task_id: str) -> ScheduledTask | None:
        """获取任务."""
        return self._tasks.get(task_id)

    async def list_tasks(
        self, enabled_only: bool = False, project_id: str | None = None
    ) -> list[ScheduledTask]:
        """列出任务."""
        tasks = list(self._tasks.values())

        if enabled_only:
            tasks = [t for t in tasks if t.enabled]

        return tasks

    async def start(self) -> None:
        """启动调度器."""
        self._running = True

        # 调度所有启用的任务
        for task in self._tasks.values():
            if task.enabled:
                self._schedule_task(task)

        logger.info("scheduler_started", task_count=len(self._tasks))

    async def stop(self) -> None:
        """停止调度器."""
        self._running = False

        # 取消所有任务
        for handle in self._task_handles.values():
            handle.cancel()

        self._task_handles.clear()
        logger.info("scheduler_stopped")

    def _schedule_task(self, task: ScheduledTask) -> None:
        """调度任务."""
        if task.trigger_type == TriggerType.CRON and task.cron:
            handle = asyncio.create_task(self._run_cron_task(task))
        elif task.trigger_type == TriggerType.INTERVAL and task.interval:
            handle = asyncio.create_task(self._run_interval_task(task))
        elif task.trigger_type == TriggerType.ONCE and task.run_at:
            handle = asyncio.create_task(self._run_once_task(task))
        else:
            logger.warning("unsupported_trigger", task_id=task.id)
            return

        self._task_handles[task.id] = handle
        logger.debug("task_scheduled", task_id=task.id)

    def _unschedule_task(self, task_id: str) -> None:
        """取消调度."""
        handle = self._task_handles.pop(task_id, None)
        if handle:
            handle.cancel()
            logger.debug("task_unscheduled", task_id=task_id)

    async def _run_cron_task(self, task: ScheduledTask) -> None:
        """运行 Cron 任务."""
        cron = task.cron
        cron_string = cron.to_cron_string()

        while self._running and task.enabled:
            try:
                # 计算下次执行时间
                now = datetime.utcnow()
                itr = croniter(cron_string, now)
                next_run = itr.get_next(datetime)
                wait_seconds = (next_run - now).total_seconds()

                task.next_run_at = next_run.isoformat()
                self._save_tasks()

                logger.debug(
                    "cron_task_waiting",
                    task_id=task.id,
                    next_run=next_run.isoformat(),
                    wait_seconds=wait_seconds,
                )

                # 等待
                await asyncio.sleep(wait_seconds)

                if not self._running or not task.enabled:
                    break

                # 执行
                await self._execute_task(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("cron_task_error", task_id=task.id, error=str(e))
                await asyncio.sleep(60)  # 出错后等待 1 分钟

    async def _run_interval_task(self, task: ScheduledTask) -> None:
        """运行间隔任务."""
        interval_seconds = task.interval.total_seconds()

        while self._running and task.enabled:
            try:
                # 执行
                await self._execute_task(task)

                # 计算下次执行时间
                next_run = datetime.utcnow() + timedelta(seconds=interval_seconds)
                task.next_run_at = next_run.isoformat()
                self._save_tasks()

                # 等待
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("interval_task_error", task_id=task.id, error=str(e))
                await asyncio.sleep(60)

    async def _run_once_task(self, task: ScheduledTask) -> None:
        """运行一次性任务."""
        try:
            run_at = datetime.fromisoformat(task.run_at)
            now = datetime.utcnow()

            if run_at > now:
                wait_seconds = (run_at - now).total_seconds()
                await asyncio.sleep(wait_seconds)

            if self._running and task.enabled:
                await self._execute_task(task)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("once_task_error", task_id=task.id, error=str(e))

    async def _execute_task(self, task: ScheduledTask) -> None:
        """执行任务."""
        import shortuuid

        logger.info("task_executing", task_id=task.id, name=task.name)

        record_id = f"rec_{shortuuid.uuid()}"
        started_at = datetime.utcnow().isoformat()

        try:
            # 1. 获取锁定的工作流
            locked = await self.planner.get_locked(task.locked_workflow_id)
            if not locked:
                raise ValueError(f"Locked workflow not found: {task.locked_workflow_id}")

            # 2. 构建继承的上下文
            inherited_context = await self._build_inherited_context(task)

            # 3. 转换工作流定义
            workflow_def = self.planner.draft_to_workflow_definition(locked.draft)

            # 4. 合并上下文到输入
            inputs = {}
            inputs.update(inherited_context.get("inputs", {}))

            # 5. 执行工作流
            result = await self.executor.execute(workflow_def, inputs)

            # 6. 记录执行
            completed_at = datetime.utcnow().isoformat()
            status = "success" if result.status.value == "completed" else "failed"

            record = TaskExecutionRecord(
                id=record_id,
                task_id=task.id,
                execution_id=result.execution_id,
                started_at=started_at,
                completed_at=completed_at,
                status=status,
                inherited_context=inherited_context,
                outputs=result.outputs,
            )

            # 7. 更新任务状态
            task.last_run_at = started_at
            task.last_run_status = status
            task.last_run_execution_id = result.execution_id
            self._save_tasks()

            # 8. 结果回流到记忆
            await self.memory.record_workflow_execution(
                workflow_id=locked.workflow_id,
                execution_id=result.execution_id,
                status=result.status.value,
                inputs=inputs,
                outputs=result.outputs,
            )

            # 9. 记录保存
            if task.id not in self._records:
                self._records[task.id] = []
            self._records[task.id].append(record)

            logger.info(
                "task_completed",
                task_id=task.id,
                execution_id=result.execution_id,
                status=status,
            )

        except Exception as e:
            logger.error("task_execution_failed", task_id=task.id, error=str(e))

            # 记录失败
            record = TaskExecutionRecord(
                id=record_id,
                task_id=task.id,
                execution_id="",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                status="failed",
                error=str(e),
            )

            task.last_run_at = started_at
            task.last_run_status = "failed"
            self._save_tasks()

            if task.id not in self._records:
                self._records[task.id] = []
            self._records[task.id].append(record)

    async def _build_inherited_context(self, task: ScheduledTask) -> dict[str, Any]:
        """构建继承的上下文."""
        context = {"inputs": {}, "memories": []}

        if task.context_policy == ContextInheritancePolicy.NONE:
            return context

        # 查询相关记忆
        from forgeclaw.memory.models import MemoryQuery

        if task.context_policy == ContextInheritancePolicy.RECENT:
            max_memories = task.context_config.get("max_memories", 10)
            query = MemoryQuery(
                workflow_id=task.locked_workflow_id,
                limit=max_memories,
            )
            memories = await self.memory.query(query)
            context["memories"] = [m.model_dump() for m in memories]

        elif task.context_policy == ContextInheritancePolicy.FILTERED:
            time_range = task.context_config.get("time_range", "7d")
            # 解析时间范围
            if time_range.endswith("d"):
                days = int(time_range[:-1])
                start_time = (datetime.utcnow() - timedelta(days=days)).isoformat()
            else:
                start_time = None

            query = MemoryQuery(
                workflow_id=task.locked_workflow_id,
                start_time=start_time,
                limit=task.context_config.get("max_memories", 10),
            )
            memories = await self.memory.query(query)
            context["memories"] = [m.model_dump() for m in memories]

        elif task.context_policy == ContextInheritancePolicy.FULL:
            query = MemoryQuery(workflow_id=task.locked_workflow_id, limit=100)
            memories = await self.memory.query(query)
            context["memories"] = [m.model_dump() for m in memories]

        return context

    async def get_execution_records(
        self, task_id: str, limit: int = 10
    ) -> list[TaskExecutionRecord]:
        """获取执行记录."""
        records = self._records.get(task_id, [])
        return sorted(records, key=lambda r: r.started_at, reverse=True)[:limit]

    async def trigger_task(self, task_id: str) -> str | None:
        """手动触发任务."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        # 立即执行
        asyncio.create_task(self._execute_task(task))
        return task_id
