"""Code Skill."""

from typing import Any

from forgeclaw.skills.base import Skill, SkillManifest


class CodeSkill(Skill):
    """Python 代码执行 Skill.

    ⚠️ 警告：MVP 实现，无沙箱隔离，仅用于测试！
    生产环境应使用 WASM 或容器沙箱。
    """

    async def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """执行 Python 代码."""
        code = inputs.get("code", "")
        code_inputs = inputs.get("inputs", {})

        if not code:
            raise ValueError("code is required")

        # 创建执行环境
        namespace = {"inputs": code_inputs, "outputs": {}}

        # 执行代码
        exec(code, namespace)

        return {"result": namespace.get("outputs", {})}
