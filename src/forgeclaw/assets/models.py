"""资产模型."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """资产类型."""

    DOCUMENT = "document"  # 文档（PDF、Word 等）
    IMAGE = "image"  # 图片
    CODE = "code"  # 代码文件
    DATA = "data"  # 数据文件（JSON、CSV 等）
    AUDIO = "audio"  # 音频
    VIDEO = "video"  # 视频
    ARCHIVE = "archive"  # 压缩包
    OTHER = "other"  # 其他


class AssetLineageNode(BaseModel):
    """资产谱系节点."""

    node_type: str = Field(..., description="节点类型: workflow/skill/asset")
    node_id: str = Field(..., description="节点 ID")
    name: str = Field(..., description="节点名称")
    timestamp: str = Field(..., description="时间戳")
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)


class AssetLineage(BaseModel):
    """资产谱系（生成链路）."""

    asset_id: str = Field(..., description="资产 ID")
    root_workflow_id: str = Field(..., description="根工作流 ID")
    execution_id: str = Field(..., description="执行 ID")

    # 生成链路
    nodes: list[AssetLineageNode] = Field(default_factory=list)

    # 依赖的资产
    source_assets: list[str] = Field(default_factory=list)

    # 生成的子资产
    derived_assets: list[str] = Field(default_factory=list)

    created_at: str = Field(..., description="创建时间")


class Asset(BaseModel):
    """创意资产."""

    id: str = Field(..., description="资产唯一标识")
    type: AssetType = Field(..., description="资产类型")

    # 元数据
    name: str = Field(..., description="资产名称")
    description: str = Field(default="", description="资产描述")
    tags: list[str] = Field(default_factory=list, description="标签")

    # 存储信息
    storage_path: str = Field(..., description="存储路径")
    size_bytes: int = Field(default=0, description="文件大小")
    format: str = Field(..., description="文件格式（扩展名）")
    checksum: str | None = Field(default=None, description="文件校验和")

    # 版本控制
    version: int = Field(default=1, description="版本号")
    previous_version: str | None = Field(default=None, description="上一版本 ID")

    # 溯源
    created_by: str = Field(..., description="创建者（工作流/节点 ID）")
    created_at: str = Field(..., description="创建时间")
    updated_at: str | None = Field(default=None, description="更新时间")
    lineage: AssetLineage | None = Field(default=None, description="生成链路")

    # 权限
    owner: str | None = Field(default=None, description="所有者")
    visibility: str = Field(default="private", description="可见性: public/private/shared")
    shared_with: list[str] = Field(default_factory=list, description="共享给的用户")

    # 额外元数据
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")
