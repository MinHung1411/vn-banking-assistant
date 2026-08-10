"""LLM factory — tách riêng để dễ đổi provider (Gemini free tier mặc định,
đổi sang OpenAI/Claude chỉ cần sửa hàm này, phần agent không cần đổi gì).

Sử dụng langchain-google-genai để tương thích tối đa với mọi môi trường deploy
(local, Docker, Hugging Face Spaces) mà không gặp xung đột dependency.
"""

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from .config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3,
    )
