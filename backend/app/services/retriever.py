"""混合检索引擎：Dense (ChromaDB+BGE-M3) + Sparse (BM25) + RRF 融合。"""

from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi
from FlagEmbedding import BGEM3FlagModel
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


class DenseRetriever:
    """基于 ChromaDB + BGE-M3 的稠密向量检索。"""

    def __init__(self) -> None:
        self.embedding_model = BGEM3FlagModel(
            settings.embedding_model_name,
            use_fp16=True,
            device=settings.embedding_device,
        )
        self.chroma_client = chromadb.PersistentClient(
            path=str(settings.chroma_db_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="merchant_docs",
            metadata={"hnsw:space": "cosine"},
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """将文本列表转为稠密向量。"""
        output = self.embedding_model.encode(
            texts, batch_size=32, max_length=512, return_dense=True
        )
        return output["dense_vecs"].tolist()

    def index(self, chunks: list[dict]) -> None:
        """将 Chunk 列表写入 ChromaDB。"""
        texts = [c["text"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]
        embeddings = self.embed(texts)
        metadatas = [
            {k: v for k, v in c.items() if k != "text"} for c in chunks
        ]
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas,
        )

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """Dense 检索，返回 top_k 条结果。"""
        k = top_k or settings.dense_top_k
        query_emb = self.embed([query])[0]
        results = self.collection.query(query_embeddings=[query_emb], n_results=k)
        return self._format_results(results)

    def _format_results(self, raw: dict) -> list[dict]:
        """将 ChromaDB 返回结果统一格式化。"""
        if not raw["ids"] or not raw["ids"][0]:
            return []
        formatted: list[dict] = []
        for i, chunk_id in enumerate(raw["ids"][0]):
            meta = raw["metadatas"][0][i] if raw.get("metadatas") and raw["metadatas"][0] else {}
            formatted.append({
                "chunk_id": chunk_id,
                "text": raw["documents"][0][i] if raw.get("documents") else "",
                "score": raw["distances"][0][i] if raw.get("distances") else 0.0,
                **meta,
            })
        return formatted


class SparseRetriever:
    """基于 BM25 的稀疏关键词检索。"""

    def __init__(self) -> None:
        self.bm25: BM25Okapi | None = None
        self.chunks: list[dict] = []
        self._tokenized_corpus: list[list[str]] = []

    def _tokenize(self, text: str) -> list[str]:
        """简单分词（中文按字，英文按空格）。"""
        return list(text.replace(" ", ""))

    def index(self, chunks: list[dict]) -> None:
        """构建 BM25 索引。"""
        self.chunks = chunks
        self._tokenized_corpus = [self._tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(self._tokenized_corpus)

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """BM25 检索，返回 top_k 条结果。"""
        if self.bm25 is None:
            return []
        k = top_k or settings.sparse_top_k
        tokenized = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized)
        top_indices = np.argsort(scores)[::-1][:k]
        return [
            {**self.chunks[i], "score": float(scores[i])}
            for i in top_indices if scores[i] > 0
        ]


def rrf_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    k: int | None = None,
) -> list[dict]:
    """Reciprocal Rank Fusion：合并两路检索结果并打分排序。"""
    k = k or settings.rrf_k
    fused: dict[str, dict] = {}

    for rank, item in enumerate(dense_results, start=1):
        cid = item["chunk_id"]
        fused[cid] = {**item, "rrf_score": 1.0 / (k + rank)}

    for rank, item in enumerate(sparse_results, start=1):
        cid = item["chunk_id"]
        score = 1.0 / (k + rank)
        if cid in fused:
            fused[cid]["rrf_score"] += score
        else:
            fused[cid] = {**item, "rrf_score": score}

    merged = list(fused.values())
    merged.sort(key=lambda x: x["rrf_score"], reverse=True)
    return merged


class HybridRetriever:
    """混合检索入口：Dense + Sparse → RRF 融合。"""

    def __init__(self) -> None:
        self.dense = DenseRetriever()
        self.sparse = SparseRetriever()

    def index(self, chunks: list[dict]) -> None:
        """同时构建 Dense 和 Sparse 索引。"""
        self.dense.index(chunks)
        self.sparse.index(chunks)

    def retrieve(self, query: str) -> list[dict]:
        """执行混合检索，返回融合去重后的候选列表。"""
        dense_results = self.dense.retrieve(query)
        sparse_results = self.sparse.retrieve(query)
        return rrf_fusion(dense_results, sparse_results)
