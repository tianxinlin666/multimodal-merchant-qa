"""FastAPI 应用入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import qa, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时预热模型，关闭时释放资源。"""
    # 预热工作（加载模型、构建索引等）在此处执行
    yield
    # 清理资源


app = FastAPI(
    title="多模态商帮问答系统 API",
    description="基于 RAG 架构的商帮历史文化智能问答系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(qa.router)
app.include_router(upload.router)


@app.get("/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "ok"}
