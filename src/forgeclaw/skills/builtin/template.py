"""Template Skill."""

from typing import Any

from jinja2 import Template

from forgeclaw.skills.base import Skill, SkillManifest


class TemplateSkill(Skill):
    """Jinja2 模板渲染 Skill."""

    async def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """渲染模板."""
        template_str = inputs.get("template", "")
        variables = inputs.get("variables", {})

        if not template_str:
            raise ValueError("template is required")

        template = Template(template_str)
        result = template.render(**variables)

        return {"result": result}
