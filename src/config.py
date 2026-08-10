"""Cấu hình tập trung, đọc từ biến môi trường / file .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM (Gemini free tier — có thể đổi sang OpenAI/Claude chỉ bằng cách viết
    # thêm 1 hàm trong src/llm.py, phần còn lại của agent không cần đổi gì)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"


    # 2 model PhoBERT đã fine-tune, push lên HuggingFace Hub
    aspect_model_repo: str = "minhunhooo/phobert-banking-aspect"
    sentiment_model_repo: str = "minhunhooo/phobert-banking-sentiment"

    # RAG
    chroma_persist_dir: str = "./chroma_banking_news"
    chroma_collection_name: str = "vn_banking_news"
    embedding_model_name: str = "intfloat/multilingual-e5-base"
    rag_top_k: int = 3

    # Dataset gốc dùng để tái tạo đúng thứ tự nhãn (id2label) lúc fine-tune —
    # xem giải thích trong src/models.py
    label_dataset_repo: str = "undertheseanlp/UTS2017_Bank"

    # Logic escalate: sentiment == negative + aspect thuộc nhóm này -> chuyển người thật xử lý
    escalate_aspects: frozenset[str] = frozenset({"SECURITY", "ACCOUNT", "CARD"})


settings = Settings()
