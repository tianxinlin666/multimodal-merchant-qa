"""文件上传接口路由。"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload/image")
async def upload_image(image: UploadFile = File(...)):
    """上传图片并返回 base64 编码，供前端预览使用。

    注意：图片理解不在本接口处理，请使用 /api/qa 接口一并上传图片并提问。
    """
    import base64

    content = await image.read()
    return {
        "filename": image.filename,
        "content_type": image.content_type,
        "size": len(content),
        "base64": base64.b64encode(content).decode("utf-8"),
    }
