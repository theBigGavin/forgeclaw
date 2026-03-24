"""资产管理器."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from forgeclaw.assets.models import Asset, AssetLineage, AssetLineageNode, AssetType

logger = structlog.get_logger()


class AssetManager:
    """资产管理器.

    管理 LLM 生成的创意资产：
    - 版本控制
    - 溯源追踪
    - 协作共享
    """

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or ".forgeclaw/assets")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 元数据存储
        self.metadata_path = self.storage_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)

        # 内存索引
        self._assets: dict[str, Asset] = {}
        self._load_all()

    def _load_all(self) -> None:
        """加载所有资产元数据."""
        for file_path in self.metadata_path.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    asset = Asset(**data)
                    self._assets[asset.id] = asset
            except Exception as e:
                logger.warning("failed_to_load_asset", file=file_path.name, error=str(e))

        logger.info("assets_loaded", count=len(self._assets))

    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def store(
        self,
        content: bytes,
        name: str,
        asset_type: AssetType,
        created_by: str,
        description: str = "",
        format: str | None = None,
        lineage: AssetLineage | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Asset:
        """存储资产.

        Args:
            content: 资产内容
            name: 资产名称
            asset_type: 资产类型
            created_by: 创建者（工作流/节点 ID）
            description: 资产描述
            format: 文件格式（如不提供，从名称推断）
            lineage: 生成链路
            metadata: 额外元数据

        Returns:
            资产对象
        """
        import shortuuid

        # 推断格式
        if not format:
            format = Path(name).suffix.lstrip(".") or "bin"

        # 生成 ID
        asset_id = f"asset_{shortuuid.uuid()}"

        # 确定存储路径
        # 按类型分目录存储
        type_dir = self.storage_path / asset_type.value
        type_dir.mkdir(exist_ok=True)

        file_path = type_dir / f"{asset_id}.{format}"

        # 写入文件
        with open(file_path, "wb") as f:
            f.write(content)

        # 计算校验和
        checksum = self._calculate_checksum(file_path)
        size_bytes = len(content)

        # 创建资产对象
        now = datetime.utcnow().isoformat()
        asset = Asset(
            id=asset_id,
            type=asset_type,
            name=name,
            description=description,
            storage_path=str(file_path.relative_to(self.storage_path)),
            size_bytes=size_bytes,
            format=format,
            checksum=checksum,
            created_by=created_by,
            created_at=now,
            lineage=lineage,
            metadata=metadata or {},
        )

        # 保存元数据
        self._assets[asset_id] = asset
        await self._save_metadata(asset)

        logger.info(
            "asset_stored",
            asset_id=asset_id,
            name=name,
            type=asset_type.value,
            size=size_bytes,
        )

        return asset

    async def _save_metadata(self, asset: Asset) -> None:
        """保存资产元数据."""
        file_path = self.metadata_path / f"{asset.id}.json"
        with open(file_path, "w") as f:
            json.dump(asset.model_dump(mode="json"), f, indent=2, default=str)

    async def get(self, asset_id: str) -> Asset | None:
        """获取资产."""
        return self._assets.get(asset_id)

    async def get_content(self, asset_id: str) -> bytes | None:
        """获取资产内容."""
        asset = self._assets.get(asset_id)
        if not asset:
            return None

        file_path = self.storage_path / asset.storage_path
        if not file_path.exists():
            return None

        with open(file_path, "rb") as f:
            return f.read()

    async def create_version(
        self,
        asset_id: str,
        content: bytes,
        change_description: str = "",
    ) -> Asset | None:
        """创建新版本."""
        old_asset = self._assets.get(asset_id)
        if not old_asset:
            return None

        # 存储新版本
        new_asset = await self.store(
            content=content,
            name=old_asset.name,
            asset_type=old_asset.type,
            created_by=old_asset.created_by,
            description=change_description or old_asset.description,
            format=old_asset.format,
            lineage=old_asset.lineage,
            metadata={**old_asset.metadata, "previous_version": asset_id},
        )

        # 更新版本链
        new_asset.version = old_asset.version + 1
        new_asset.previous_version = asset_id
        await self._save_metadata(new_asset)

        # 更新旧资产
        old_asset.metadata["next_version"] = new_asset.id
        await self._save_metadata(old_asset)

        logger.info(
            "asset_version_created",
            old_id=asset_id,
            new_id=new_asset.id,
            version=new_asset.version,
        )

        return new_asset

    async def list_assets(
        self,
        asset_type: AssetType | None = None,
        created_by: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Asset]:
        """列出资产."""
        results = list(self._assets.values())

        if asset_type:
            results = [a for a in results if a.type == asset_type]

        if created_by:
            results = [a for a in results if a.created_by == created_by]

        if tags:
            results = [a for a in results if any(t in a.tags for t in tags)]

        # 按创建时间倒序
        results.sort(key=lambda a: a.created_at, reverse=True)

        return results[offset : offset + limit]

    async def delete(self, asset_id: str) -> bool:
        """删除资产."""
        asset = self._assets.get(asset_id)
        if not asset:
            return False

        # 删除文件
        file_path = self.storage_path / asset.storage_path
        if file_path.exists():
            file_path.unlink()

        # 删除元数据
        meta_path = self.metadata_path / f"{asset_id}.json"
        if meta_path.exists():
            meta_path.unlink()

        # 从内存移除
        del self._assets[asset_id]

        logger.info("asset_deleted", asset_id=asset_id)
        return True

    async def get_lineage(self, asset_id: str) -> AssetLineage | None:
        """获取资产的生成链路."""
        asset = self._assets.get(asset_id)
        return asset.lineage if asset else None

    async def build_lineage_from_execution(
        self,
        execution_id: str,
        workflow_id: str,
        node_results: dict[str, Any],
    ) -> AssetLineage:
        """从执行结果构建谱系.

        Args:
            execution_id: 执行 ID
            workflow_id: 工作流 ID
            node_results: 节点执行结果

        Returns:
            资产谱系
        """
        import shortuuid

        now = datetime.utcnow().isoformat()

        nodes = []
        for node_id, result in node_results.items():
            node = AssetLineageNode(
                node_type="skill" if result.get("skill_id") else "workflow",
                node_id=node_id,
                name=result.get("name", node_id),
                timestamp=result.get("start_time", now),
                inputs=result.get("inputs", {}),
                outputs=result.get("outputs", {}),
            )
            nodes.append(node)

        lineage = AssetLineage(
            asset_id=f"asset_{shortuuid.uuid()}",  # 占位，实际存储时会更新
            root_workflow_id=workflow_id,
            execution_id=execution_id,
            nodes=nodes,
            created_at=now,
        )

        return lineage

    async def share(
        self,
        asset_id: str,
        users: list[str],
        visibility: str = "shared",
    ) -> bool:
        """共享资产.

        Args:
            asset_id: 资产 ID
            users: 共享给的用户列表
            visibility: 可见性级别
        """
        asset = self._assets.get(asset_id)
        if not asset:
            return False

        asset.visibility = visibility
        asset.shared_with = list(set(asset.shared_with + users))
        asset.updated_at = datetime.utcnow().isoformat()

        await self._save_metadata(asset)

        logger.info("asset_shared", asset_id=asset_id, users=users)
        return True

    async def update_metadata(
        self,
        asset_id: str,
        updates: dict[str, Any],
    ) -> bool:
        """更新资产元数据."""
        asset = self._assets.get(asset_id)
        if not asset:
            return False

        allowed_fields = ["name", "description", "tags", "metadata"]

        for key, value in updates.items():
            if key in allowed_fields and hasattr(asset, key):
                setattr(asset, key, value)

        asset.updated_at = datetime.utcnow().isoformat()
        await self._save_metadata(asset)

        logger.info("asset_metadata_updated", asset_id=asset_id)
        return True
