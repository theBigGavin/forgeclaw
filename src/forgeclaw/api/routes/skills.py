"""Skill 路由."""

from typing import Any

from fastapi import APIRouter

from forgeclaw.skills.registry import SkillRegistry

router = APIRouter()
registry = SkillRegistry()


@router.get("", response_model=list)
async def list_skills() -> list[dict[str, Any]]:
    """列出所有 Skill."""
    manifests = registry.list_skills()
    return [
        {
            "id": m.id,
            "name": m.name,
            "version": m.version,
            "description": m.description,
        }
        for m in manifests
    ]


@router.get("/{skill_id}", response_model=dict)
async def get_skill(skill_id: str) -> dict[str, Any]:
    """获取 Skill 详情."""
    try:
        skill = registry.get(skill_id)
        return {
            "id": skill.manifest.id,
            "name": skill.manifest.name,
            "version": skill.manifest.version,
            "description": skill.manifest.description,
            "input_schema": skill.manifest.input_schema,
            "output_schema": skill.manifest.output_schema,
        }
    except KeyError:
        return {"error": "Skill not found"}
