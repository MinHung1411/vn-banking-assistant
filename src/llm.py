"""LLM factory — hỗ trợ fallback nhiều model Gemini active (2026) & tự động retry khi dính Rate Limit (429)."""

from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import settings


@lru_cache(maxsize=1)
def get_llm():
    primary_model = settings.gemini_model or "gemini-flash-latest"
    
    primary_llm = ChatGoogleGenerativeAI(
        model=primary_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3,
        max_retries=3,
    )
    
    # Danh sách các model đang hoạt động thực tế trên Google GenAI API (2026)
    fallback_models = ["gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash"]
    fallbacks = []
    
    for m in fallback_models:
        if m != primary_model:
            fallbacks.append(
                ChatGoogleGenerativeAI(
                    model=m,
                    google_api_key=settings.gemini_api_key,
                    temperature=0.3,
                    max_retries=2,
                )
            )
            
    if fallbacks:
        return primary_llm.with_fallbacks(fallbacks)
    return primary_llm
