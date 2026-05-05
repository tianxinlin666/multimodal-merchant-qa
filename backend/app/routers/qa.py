"""问答接口路由。"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.services.orchestrator import get_pipeline, QAResponse

router = APIRouter(prefix="/api", tags=["qa"])


@router.post("/qa", response_model=QAResponse)
async def ask_question(
    question: str = Form(..., description="用户问题"),
    image: UploadFile | None = File(None, description="可选图片"),
) -> QAResponse:
    """多模态问答接口。

    支持纯文本问答和图文联合问答。上传图片时，后端会先调用
    Qwen2-VL 进行图片理解，扩充 Query 后再走 RAG 流程。
    """
    import base64

    image_base64: str | None = None
    if image is not None:
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    pipeline = get_pipeline()
    return await pipeline.answer(question, image_base64)
