"""Skill 注册表."""

from typing import Any

import structlog

from forgeclaw.skills.base import Skill, SkillManifest
from forgeclaw.skills.builtin.code import CodeSkill
from forgeclaw.skills.builtin.http import HttpSkill
from forgeclaw.skills.builtin.template import TemplateSkill

logger = structlog.get_logger()


class SkillRegistry:
    """Skill 注册表.

    MVP 使用内存注册，后续可扩展为数据库/远程服务.
    """

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._register_builtin_skills()

    def _register_builtin_skills(self) -> None:
        """注册内置 Skill."""
        # HTTP Skill
        self.register(
            HttpSkill(
                SkillManifest(
                    id="http_request",
                    name="HTTP 请求",
                    description="发送 HTTP 请求",
                    input_schema={
                        "url": {"type": "string"},
                        "method": {"type": "string", "default": "GET"},
                        "headers": {"type": "object", "default": {}},
                        "body": {"type": "any"},
                    },
                    output_schema={
                        "status_code": {"type": "integer"},
                        "body": {"type": "any"},
                        "headers": {"type": "object"},
                    },
                )
            )
        )

        # Template Skill
        self.register(
            TemplateSkill(
                SkillManifest(
                    id="template_render",
                    name="模板渲染",
                    description="渲染 Jinja2 模板",
                    input_schema={
                        "template": {"type": "string"},
                        "variables": {"type": "object", "default": {}},
                    },
                    output_schema={
                        "result": {"type": "string"},
                    },
                )
            )
        )

        # Code Skill
        self.register(
            CodeSkill(
                SkillManifest(
                    id="python_code",
                    name="Python 代码执行",
                    description="执行 Python 代码",
                    input_schema={
                        "code": {"type": "string"},
                        "inputs": {"type": "object", "default": {}},
                    },
                    output_schema={
                        "result": {"type": "any"},
                    },
                )
            )
        )

        logger.info("builtin_skills_registered", count=len(self._skills))

    def register(self, skill: Skill) -> None:
        """注册 Skill."""
        key = f"{skill.manifest.id}@{skill.manifest.version}"
        self._skills[key] = skill
        logger.debug("skill_registered", key=key)

    def get(self, skill_id: str, version: str | None = None) -> Skill:
        """获取 Skill.

        Args:
            skill_id: Skill ID
            version: 版本，None 表示最新版本

        Returns:
            Skill 实例

        Raises:
            KeyError: Skill 不存在
        """
        if version:
            key = f"{skill_id}@{version}"
            if key in self._skills:
                return self._skills[key]
            raise KeyError(f"Skill not found: {key}")

        # 查找最新版本
        matching = [
            (k, s) for k, s in self._skills.items() if k.startswith(f"{skill_id}@")
        ]
        if not matching:
            raise KeyError(f"Skill not found: {skill_id}")

        # 简单的版本比较（TODO: 使用语义化版本库）
        latest = max(matching, key=lambda x: x[0])
        return latest[1]

    def list_skills(self) -> list[SkillManifest]:
        """列出所有 Skill."""
        return [s.manifest for s in self._skills.values()]

    def unregister(self, skill_id: str, version: str) -> bool:
        """注销 Skill."""
        key = f"{skill_id}@{version}"
        if key in self._skills:
            del self._skills[key]
            return True
        return False
