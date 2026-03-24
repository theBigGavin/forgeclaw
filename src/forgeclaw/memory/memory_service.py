"""结构化记忆服务."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from forgeclaw.memory.models import (
    ContextSnapshot,
    MemoryEntry,
    MemoryQuery,
    MemoryType,
)

logger = structlog.get_logger()


class MemoryService:
    """结构化记忆服务.

    提供：
    - 结构化存储（替代 Markdown 文本）
    - 关系图谱（工作流、Skill、资产关联）
    - 语义检索（向量相似度）
    - 上下文快照（用于注入工作流）
    """

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or ".forgeclaw/memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 内存索引（MVP 简化版）
        self._entries: dict[str, MemoryEntry] = {}
        self._load_all()

    def _load_all(self) -> None:
        """加载所有记忆."""
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    entry = MemoryEntry(**data)
                    self._entries[entry.id] = entry
            except Exception as e:
                logger.warning("failed_to_load_memory", file=file_path.name, error=str(e))

        logger.info("memory_loaded", count=len(self._entries))

    async def store(self, entry: MemoryEntry) -> str:
        """存储记忆.

        Args:
            entry: 记忆条目

        Returns:
            记忆 ID
        """
        # 更新时间
        entry.updated_at = datetime.utcnow().isoformat()

        # 保存到内存
        self._entries[entry.id] = entry

        # 持久化到文件
        file_path = self.storage_path / f"{entry.id}.json"
        with open(file_path, "w") as f:
            json.dump(entry.model_dump(mode="json"), f, indent=2, default=str)

        logger.debug("memory_stored", memory_id=entry.id, type=entry.type)
        return entry.id

    async def get(self, memory_id: str) -> MemoryEntry | None:
        """获取记忆."""
        return self._entries.get(memory_id)

    async def query(self, query: MemoryQuery) -> list[MemoryEntry]:
        """查询记忆.

        支持：
        - 精确查询（按 ID、类型、时间）
        - 语义查询（向量相似度）
        - 关系查询（图遍历）
        """
        results = list(self._entries.values())

        # 精确过滤
        if query.memory_type:
            results = [r for r in results if r.type == query.memory_type]

        if query.workflow_id:
            results = [r for r in results if r.workflow_id == query.workflow_id]

        if query.execution_id:
            results = [r for r in results if r.execution_id == query.execution_id]

        if query.project_id:
            results = [r for r in results if r.project_id == query.project_id]

        # 时间范围过滤
        if query.start_time:
            results = [r for r in results if r.created_at >= query.start_time]

        if query.end_time:
            results = [r for r in results if r.created_at <= query.end_time]

        # 语义检索（简化版：基于文本匹配）
        if query.semantic_query:
            # MVP：使用简单的文本匹配，生产环境应使用向量数据库
            query_lower = query.semantic_query.lower()
            scored_results = []
            for entry in results:
                score = self._calculate_relevance(entry, query_lower)
                if score >= query.similarity_threshold:
                    scored_results.append((entry, score))

            # 按相关度排序
            scored_results.sort(key=lambda x: x[1], reverse=True)
            results = [r[0] for r in scored_results[: query.top_k]]

        # 关系查询
        if query.related_to:
            results = self._query_relations(query.related_to, query.relation_depth)

        # 分页
        results = results[query.offset : query.offset + query.limit]

        return results

    def _calculate_relevance(self, entry: MemoryEntry, query: str) -> float:
        """计算相关性分数（简化版）."""
        score = 0.0
        content_text = json.dumps(entry.content, ensure_ascii=False).lower()

        # 完全匹配
        if query in content_text:
            score += 0.5

        # 关键词匹配
        query_words = query.split()
        for word in query_words:
            if word in content_text:
                score += 0.3 / len(query_words)

        # 元数据匹配
        metadata_text = json.dumps(entry.metadata, ensure_ascii=False).lower()
        if query in metadata_text:
            score += 0.2

        return min(score, 1.0)

    def _query_relations(self, memory_id: str, depth: int) -> list[MemoryEntry]:
        """查询相关记忆（图遍历）."""
        results = []
        visited = {memory_id}
        queue = [(memory_id, 0)]

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_depth >= depth:
                continue

            entry = self._entries.get(current_id)
            if not entry:
                continue

            # 收集关联记忆
            related_ids = (
                entry.related_workflows
                + entry.related_skills
                + entry.related_assets
                + entry.child_memories
            )

            if entry.parent_memory:
                related_ids.append(entry.parent_memory)

            for related_id in related_ids:
                if related_id not in visited:
                    visited.add(related_id)
                    related_entry = self._entries.get(related_id)
                    if related_entry:
                        results.append(related_entry)
                        queue.append((related_id, current_depth + 1))

        return results

    async def build_context(
        self,
        project_id: str | None = None,
        session_id: str | None = None,
        workflow_id: str | None = None,
        semantic_query: str | None = None,
        max_depth: int = 3,
    ) -> ContextSnapshot:
        """构建上下文快照.

        Args:
            project_id: 项目 ID
            session_id: 会话 ID
            workflow_id: 工作流 ID
            semantic_query: 语义查询
            max_depth: 关系遍历深度

        Returns:
            上下文快照
        """
        import shortuuid

        snapshot_id = f"ctx_{shortuuid.uuid()}"
        created_at = datetime.utcnow().isoformat()

        # 收集相关记忆
        recent_memories = []
        relevant_memories = []
        project_memories = []

        # 1. 最近执行的记忆
        if workflow_id:
            query = MemoryQuery(workflow_id=workflow_id, limit=5)
            recent_memories = await self.query(query)

        # 2. 语义检索
        if semantic_query:
            query = MemoryQuery(semantic_query=semantic_query, top_k=5)
            relevant_memories = await self.query(query)

        # 3. 项目级记忆
        if project_id:
            query = MemoryQuery(project_id=project_id, limit=10)
            project_memories = await self.query(query)

        # 生成摘要
        summary_parts = []
        if recent_memories:
            summary_parts.append(f"最近 {len(recent_memories)} 条执行记录")
        if relevant_memories:
            summary_parts.append(f"{len(relevant_memories)} 条相关记忆")
        if project_memories:
            summary_parts.append(f"项目历史 {len(project_memories)} 条")

        summary = "，".join(summary_parts) if summary_parts else "无上下文"

        return ContextSnapshot(
            snapshot_id=snapshot_id,
            project_id=project_id,
            session_id=session_id,
            recent_memories=recent_memories,
            relevant_memories=relevant_memories,
            project_memories=project_memories,
            summary=summary,
            created_at=created_at,
        )

    async def delete(self, memory_id: str) -> bool:
        """删除记忆."""
        if memory_id not in self._entries:
            return False

        # 删除文件
        file_path = self.storage_path / f"{memory_id}.json"
        if file_path.exists():
            file_path.unlink()

        # 从内存移除
        del self._entries[memory_id]

        logger.info("memory_deleted", memory_id=memory_id)
        return True

    async def update_relations(
        self,
        memory_id: str,
        add_related: dict[str, list[str]] | None = None,
        remove_related: dict[str, list[str]] | None = None,
    ) -> bool:
        """更新记忆关系.

        Args:
            memory_id: 记忆 ID
            add_related: 添加的关系，如 {"related_workflows": ["wf_xxx"]}
            remove_related: 移除的关系
        """
        entry = self._entries.get(memory_id)
        if not entry:
            return False

        # 添加关系
        if add_related:
            for key, values in add_related.items():
                current = getattr(entry, key, [])
                setattr(entry, key, list(set(current + values)))

        # 移除关系
        if remove_related:
            for key, values in remove_related.items():
                current = getattr(entry, key, [])
                setattr(entry, key, [v for v in current if v not in values])

        # 保存
        await self.store(entry)
        return True

    async def record_workflow_execution(
        self,
        workflow_id: str,
        execution_id: str,
        status: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        project_id: str | None = None,
    ) -> str:
        """记录工作流执行."""
        import shortuuid

        from forgeclaw.memory.models import WorkflowMemoryContent

        entry = MemoryEntry(
            id=f"mem_{shortuuid.uuid()}",
            type=MemoryType.WORKFLOW,
            workflow_id=workflow_id,
            execution_id=execution_id,
            project_id=project_id,
            content=WorkflowMemoryContent(
                workflow_id=workflow_id,
                execution_id=execution_id,
                status=status,
                inputs=inputs,
                outputs=outputs,
            ).model_dump(),
            created_at=datetime.utcnow().isoformat(),
        )

        return await self.store(entry)

    async def record_skill_execution(
        self,
        skill_id: str,
        skill_version: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        execution_time_ms: int,
        workflow_id: str | None = None,
        execution_id: str | None = None,
    ) -> str:
        """记录 Skill 执行."""
        import shortuuid

        from forgeclaw.memory.models import SkillMemoryContent

        entry = MemoryEntry(
            id=f"mem_{shortuuid.uuid()}",
            type=MemoryType.SKILL,
            workflow_id=workflow_id,
            execution_id=execution_id,
            content=SkillMemoryContent(
                skill_id=skill_id,
                skill_version=skill_version,
                inputs=inputs,
                outputs=outputs,
                execution_time_ms=execution_time_ms,
            ).model_dump(),
            created_at=datetime.utcnow().isoformat(),
        )

        return await self.store(entry)
