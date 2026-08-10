"""LLM factory — hỗ trợ fallback nhiều model Gemini active & xoay vòng nhiều API key tự động khi dính Rate Limit (429)."""

from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import settings


@lru_cache(maxsize=16)
def get_llm(api_key: str | None = None, model: str | None = None):
    """Tạo hoặc lấy LLM instance.

    Hỗ trợ truyền api_key/model trực tiếp từ UI/API, hoặc tự động đọc từ settings.
    Hỗ trợ truyền nhiều API Key cách nhau bởi dấu phẩy (key1,key2) để xoay vòng fallback.
    """
    raw_keys = (api_key or settings.gemini_api_key or "").strip()
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    if not keys:
        keys = [""]

    primary_model = model or settings.gemini_model or "gemini-1.5-flash"

    # Danh sách model Gemini thực tế hỗ trợ fallback nếu model chính bị nghẽn
    valid_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-flash-latest"]

    # Tạo danh sách các cặp (key, model) để fallback
    candidates = []
    for k in keys:
        candidates.append((k, primary_model))
        for m in valid_models:
            if m != primary_model and (k, m) not in candidates:
                candidates.append((k, m))

    llms = []
    for k, m in candidates:
        kwargs = {"model": m, "temperature": 0.3, "max_retries": 2}
        if k:
            kwargs["google_api_key"] = k
        llms.append(ChatGoogleGenerativeAI(**kwargs))

    primary_llm = llms[0]
    fallbacks = llms[1:]

    if fallbacks:
        return primary_llm.with_fallbacks(fallbacks)
    return primary_llm

