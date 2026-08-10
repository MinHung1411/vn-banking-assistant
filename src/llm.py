"""LLM factory — hỗ trợ fallback nhiều model Gemini & tự động retry khi gặp Rate Limit (429)."""

from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import settings


@lru_cache(maxsize=1)
def get_llm():
    primary_model = settings.gemini_model or "gemini-1.5-flash"
    
    primary_llm = ChatGoogleGenerativeAI(
        model=primary_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3,
        max_retries=3,
    )
    
    # Các model dự phòng nếu primary model bị dính 429 Quota Exceeded
    fallback_models = ["gemini-2.0-flash", "gemini-1.5-flash-8b", "gemini-1.5-flash"]
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
