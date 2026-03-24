"""HTTP Skill."""

from typing import Any

import httpx

from forgeclaw.skills.base import Skill, SkillManifest


class HttpSkill(Skill):
    """HTTP 请求 Skill."""

    async def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """执行 HTTP 请求."""
        url = inputs.get("url")
        method = inputs.get("method", "GET").upper()
        headers = inputs.get("headers", {})
        body = inputs.get("body")

        if not url:
            raise ValueError("url is required")

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=body)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=body)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # 尝试解析 JSON
            try:
                body_data = response.json()
            except Exception:
                body_data = response.text

            return {
                "status_code": response.status_code,
                "body": body_data,
                "headers": dict(response.headers),
            }
