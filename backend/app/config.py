"""应用配置管理。"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置，支持 .env 文件覆盖。"""

    # --- 项目路径 ---
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = project_root / "data"
    raw_txt_dir: Path = data_dir / "raw_txt"
    cleaned_dir: Path = data_dir / "cleaned"
    chroma_db_dir: Path = data_dir / "chroma_db"

    # --- 模型服务端点 ---
    llm_base_url: str = "http://localhost:8000/v1"
    llm_api_key: str = "your-api-key-here"
    llm_model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    vl_service_url: str = "http://localhost:8001"

    # --- Embedding ---
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_device: str = "cuda"

    # --- Reranker ---
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_device: str = "cuda"

    # --- 检索参数 ---
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rerank_top_k: int = 8
    chunk_size: int = 500

    # --- RRF 融合 ---
    rrf_k: int = 60

    # --- LLM 生成 ---
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
