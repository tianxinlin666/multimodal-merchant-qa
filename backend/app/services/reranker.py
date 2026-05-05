"""Cross-Encoder 重排序：bge-reranker-v2-m3 精排 + 相邻块补全。"""

from __future__ import annotations

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import settings


class RerankerService:
    """基于 bge-reranker-v2-m3 的 Cross-Encoder 重排序。"""

    def __init__(self) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(settings.reranker_model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            settings.reranker_model_name,
        )
        self.model.to(settings.reranker_device)
        self.model.eval()

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int | None = None,
    ) -> list[dict]:
        """对候选段落逐一计算相关性分数，返回精排后的 top-k 结果。"""
        k = top_k or settings.rerank_top_k
        if not candidates:
            return []

        pairs = [[query, c["text"][:512]] for c in candidates]
        with torch.no_grad():
            inputs = self.tokenizer(
                [p[0] for p in pairs],
                [p[1] for p in pairs],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.model.device)
            scores = self.model(**inputs, return_dict=True).logits.view(-1)

        for i, candidate in enumerate(candidates):
            candidate["rerank_score"] = float(scores[i])

        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:k]


def expand_context(
    top_chunks: list[dict],
    all_chunks: dict[str, dict],
) -> list[dict]:
    """相邻块补全：为命中 Chunk 自动补全前后相邻块（同一章节内）。"""
    expanded: dict[str, dict] = {}
    for chunk in top_chunks:
        cid = chunk["chunk_id"]
        expanded[cid] = chunk
        chapter = chunk.get("chapter_title", "")
        if chunk.get("prev_chunk_id"):
            prev = all_chunks.get(chunk["prev_chunk_id"])
            if prev and prev.get("chapter_title") == chapter:
                expanded[chunk["prev_chunk_id"]] = prev
        if chunk.get("next_chunk_id"):
            nxt = all_chunks.get(chunk["next_chunk_id"])
            if nxt and nxt.get("chapter_title") == chapter:
                expanded[chunk["next_chunk_id"]] = nxt
    return list(expanded.values())
