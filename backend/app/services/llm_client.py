"""LLM 客户端：通过 OpenAI 兼容 API 调用 Qwen2.5-7B-Instruct (vLLM)。"""

from __future__ import annotations

from openai import OpenAI

from app.config import settings

QA_PROMPT = """基于以下从历史文献中检索到的信息回答用户的问题。如果信息不足以回答问题，请如实告知。

用户问题: {question}

相关资料:
{context}

回答:"""


class LLMClient:
    """Qwen2.5-7B-Instruct 文本生成客户端。"""

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )

    def generate(self, question: str, contexts: list[str]) -> str:
        """根据问题和检索上下文生成最终答案。"""
        context_str = "\n".join(f"- {ctx}" for ctx in contexts)
        prompt = QA_PROMPT.format(question=question, context=context_str)

        response = self.client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        return response.choices[0].message.content or ""


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例。"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
