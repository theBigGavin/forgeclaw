"""资产管理路由."""

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from forgeclaw.assets.asset_manager import AssetManager
from forgeclaw.assets.models import Asset, AssetType

router = APIRouter()
asset_manager = AssetManager()


class UpdateMetadataRequest(BaseModel):
    """更新元数据请求."""
    updates: dict[str, Any]


class ShareRequest(BaseModel):
    """共享请求 (后端内部格式)."""
    users: list[str]
    visibility: str = "shared"


class ShareRequestFrontend(BaseModel):
    """共享请求 (前端格式)."""
    target_project_id: str


class CreateVersionRequest(BaseModel):
    """创建版本请求."""
    change_description: str = ""


# ========== 基础 CRUD ==========

@router.post("/upload", response_model=Asset)
async def upload_asset(
    file: UploadFile = File(...),
    name: str = Form(...),
    asset_type: AssetType = Form(...),
    created_by: str = Form(...),
    description: str = Form(""),
) -> Asset:
    """上传资产."""
    content = await file.read()

    asset = await asset_manager.store(
        content=content,
        name=name,
        asset_type=asset_type,
        created_by=created_by,
        description=description,
        format=file.filename.split(".")[-1] if "." in file.filename else None,
    )
    return asset


@router.post("", response_model=Asset)
async def upload_asset_simple(
    file: UploadFile = File(...),
    name: str = Form(""),
    project_id: str = Form("default"),
) -> Asset:
    """上传资产 (前端兼容简化格式)."""
    content = await file.read()
    
    # 自动检测 asset_type
    filename = file.filename or ""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    asset_type_map = {
        "txt": AssetType.TEXT,
        "md": AssetType.TEXT,
        "json": AssetType.CODE,
        "py": AssetType.CODE,
        "js": AssetType.CODE,
        "ts": AssetType.CODE,
        "png": AssetType.IMAGE,
        "jpg": AssetType.IMAGE,
        "jpeg": AssetType.IMAGE,
        "gif": AssetType.IMAGE,
        "mp3": AssetType.AUDIO,
        "wav": AssetType.AUDIO,
        "mp4": AssetType.VIDEO,
        "pdf": AssetType.BINARY,
    }
    asset_type = asset_type_map.get(ext, AssetType.BINARY)
    
    asset_name = name or filename or f"asset_{id(content)}"

    asset = await asset_manager.store(
        content=content,
        name=asset_name,
        asset_type=asset_type,
        created_by=project_id,
        description="",
        format=ext if ext else None,
    )
    return asset


@router.get("", response_model=list)
async def list_assets(
    asset_type: AssetType | None = None,
    created_by: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """列出资产."""
    assets = await asset_manager.list_assets(
        asset_type=asset_type,
        created_by=created_by,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": a.id,
            "name": a.name,
            "asset_type": a.type.value if hasattr(a.type, 'value') else str(a.type),
            "type": a.type.value if hasattr(a.type, 'value') else str(a.type),  # 前端兼容
            "size_bytes": a.size_bytes,
            "format": a.format,
            "created_at": a.created_at,
            "updated_at": a.created_at,  # 前端兼容
            "created_by": a.created_by,
            "project_id": a.created_by,  # 前端兼容
            "current_version": "1.0",  # 前端兼容
        }
        for a in assets
    ]


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str) -> Asset:
    """获取资产详情."""
    asset = await asset_manager.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/{asset_id}/content")
async def get_asset_content(asset_id: str):
    """获取资产内容."""
    from fastapi.responses import Response

    asset = await asset_manager.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    content = await asset_manager.get_content(asset_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Asset content not found")

    # 根据类型设置 content-type
    content_type_map = {
        "pdf": "application/pdf",
        "json": "application/json",
        "txt": "text/plain",
        "md": "text/markdown",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    content_type = content_type_map.get(asset.format, "application/octet-stream")

    return Response(content=content, media_type=content_type)


@router.delete("/{asset_id}", response_model=dict)
async def delete_asset(asset_id: str) -> dict[str, Any]:
    """删除资产."""
    success = await asset_manager.delete(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"asset_id": asset_id, "status": "deleted"}


# ========== 版本管理 ==========

@router.get("/{asset_id}/versions", response_model=list)
async def list_asset_versions(asset_id: str) -> list[dict[str, Any]]:
    """列出资产版本历史 (前端兼容)."""
    asset = await asset_manager.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # 返回当前版本作为唯一版本 (MVP 简化)
    return [
        {
            "id": f"{asset_id}_v1",
            "version": "1.0",
            "created_at": asset.created_at,
            "created_by": asset.created_by,
            "size_bytes": asset.size_bytes,
            "checksum": "",
            "comment": "Initial version",
        }
    ]


@router.post("/{asset_id}/version", response_model=Asset)
async def create_version(
    asset_id: str,
    file: UploadFile = File(...),
    change_description: str = Form(""),
) -> Asset:
    """创建新版本."""
    content = await file.read()
    asset = await asset_manager.create_version(asset_id, content, change_description)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/{asset_id}/versions", response_model=Asset)
async def create_version_alias(
    asset_id: str,
    file: UploadFile = File(...),
) -> Asset:
    """创建新版本 (前端兼容复数路径)."""
    content = await file.read()
    asset = await asset_manager.create_version(asset_id, content, "")
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# ========== 元数据和共享 ==========

@router.put("/{asset_id}/metadata", response_model=dict)
async def update_metadata(asset_id: str, request: UpdateMetadataRequest) -> dict[str, Any]:
    """更新资产元数据."""
    success = await asset_manager.update_metadata(asset_id, request.updates)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"asset_id": asset_id, "status": "updated"}


@router.post("/{asset_id}/share", response_model=dict)
async def share_asset(asset_id: str, request: ShareRequest) -> dict[str, Any]:
    """共享资产."""
    success = await asset_manager.share(asset_id, request.users, request.visibility)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"asset_id": asset_id, "status": "shared"}


@router.post("/{asset_id}/share", response_model=dict)
async def share_asset_frontend(asset_id: str, request: ShareRequestFrontend) -> dict[str, Any]:
    """共享资产 (前端兼容格式)."""
    # 转换前端格式为内部格式
    users = [request.target_project_id]
    success = await asset_manager.share(asset_id, users, "shared")
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"asset_id": asset_id, "status": "shared", "target_project_id": request.target_project_id}
