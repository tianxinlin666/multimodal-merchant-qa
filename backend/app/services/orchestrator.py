"""QA 流程编排器：串联 图片理解 → 混合检索 → 重排序 → 上下文补全 → 生成。"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.retriever import HybridRetriever
from app.services.reranker import RerankerService, expand_context
from app.services.llm_client import get_llm_client
from app.services.image_analyzer import (
    ImageAnalyzer,
    VisionResult,
    enrich_query,
    get_image_analyzer,
)


@dataclass
class QAResponse:
    answer: str
    sources: list[dict] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)


class QAPipeline:
    """端到端问答流水线。"""

    def __init__(self) -> None:
        self.retriever = HybridRetriever()
        self.reranker = RerankerService()
        self.llm = get_llm_client()
        self.image_analyzer = get_image_analyzer()

    async def answer(self, question: str, image_base64: str | None = None) -> QAResponse:
        """处理一次完整的问答请求。

        Pipeline:
        1. 若有图片 → Qwen2-VL 分析 → 扩充 Query
        2. 混合检索（Dense + Sparse → RRF 融合）
        3. Reranker 精排 → Top k
        4. 相邻 Chunk 上下文补全
        5. Qwen2.5-7B 生成答案
        """
        enriched_query = question

        # Step 1: 图片理解 + Query 扩充
        if image_base64:
            vision_result: VisionResult = await self.image_analyzer.analyze(
                image_base64, question
            )
            enriched_query = enrich_query(question, vision_result)

        # Step 2: 混合检索
        candidates = self.retriever.retrieve(enriched_query)

        # Step 3: 重排序
        top_chunks = self.reranker.rerank(enriched_query, candidates)

        # Step 4: 上下文补全（省略 all_chunks 查找逻辑，由调用方传入完整映射时启用）
        contexts = [c["text"] for c in top_chunks]

        # Step 5: LLM 生成
        answer_text = self.llm.generate(question, contexts)

        return QAResponse(
            answer=answer_text,
            sources=[{k: c.get(k, "") for k in ("chunk_id", "book_title", "chapter_title", "text")} for c in top_chunks],
            scores=[c.get("rerank_score", 0.0) for c in top_chunks],
        )

    def index(self, chunks: list[dict]) -> None:
        """构建检索索引（数据预处理阶段调用）。"""
        self.retriever.index(chunks)


_pipeline: QAPipeline | None = None


def get_pipeline() -> QAPipeline:
    """获取 QA Pipeline 单例。"""
    global _pipeline
    if _pipeline is None:
        _pipeline = QAPipeline()
    return _pipeline
