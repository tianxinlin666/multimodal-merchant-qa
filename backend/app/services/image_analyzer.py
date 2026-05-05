"""图片理解服务：Qwen2-VL-7B-Instruct 多模态分析。"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field

import httpx
from PIL import Image

from app.config import settings


@dataclass
class VisionResult:
    caption: str = ""
    visible_text: str = ""
    keywords: list[str] = field(default_factory=list)


class ImageAnalyzer:
    """通过 Qwen2-VL 服务分析图片内容，提取描述、文字、关键词。"""

    def __init__(self) -> None:
        self.base_url = settings.vl_service_url

    async def analyze(self, image_base64: str, user_question: str) -> VisionResult:
        """调用 Qwen2-VL 分析图片，返回结构化理解结果。"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/analyze_image",
                json={"image": image_base64, "question": user_question},
            )
            resp.raise_for_status()
            data = resp.json()
            return VisionResult(
                caption=data.get("caption", ""),
                visible_text=data.get("visible_text", ""),
                keywords=data.get("keywords", []),
            )

    @staticmethod
    def decode_base64_image(image_base64: str) -> Image.Image:
        """将 base64 字符串解码为 PIL Image。"""
        image_bytes = base64.b64decode(image_base64)
        return Image.open(io.BytesIO(image_bytes))


def enrich_query(original_question: str, vision_result: VisionResult) -> str:
    """将图片分析结果与原始问题拼接，构建增强查询。"""
    parts = [
        original_question,
        vision_result.caption,
        vision_result.visible_text,
        " ".join(vision_result.keywords),
    ]
    return " ".join(p for p in parts if p)


_analyzer: ImageAnalyzer | None = None


def get_image_analyzer() -> ImageAnalyzer:
    """获取图片分析服务单例。"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ImageAnalyzer()
    return _analyzer
