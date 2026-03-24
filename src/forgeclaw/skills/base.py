"""Skill 基类."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class SkillManifest(BaseModel):
    """Skill 清单."""

    id: str = Field(..., description="Skill 唯一标识")
    name: str = Field(..., description="Skill 可读名称")
    version: str = Field(default="1.0.0", description="语义化版本")
    description: str = Field(default="", description="Skill 描述")

    # 输入输出契约
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)

    # 执行配置
    timeout: int = Field(default=300, description="默认超时(秒)")


class Skill(ABC):
    """Skill 基类."""

    def __init__(self, manifest: SkillManifest):
        self.manifest = manifest

    @abstractmethod
    async def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """执行 Skill.

        Args:
            inputs: 输入参数

        Returns:
            输出结果
        """
        pass

    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """验证输入（可选）."""
        return True
