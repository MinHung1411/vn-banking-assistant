"""Load lại Chroma index (đã build ở Kaggle, mục 9 của notebook fine-tune)
và cung cấp hàm retrieve() cho agent.

Trước khi chạy: tải `chroma_banking_news.zip` từ Kaggle output, giải nén vào
đúng thư mục `CHROMA_PERSIST_DIR` (mặc định `./chroma_banking_news`).
"""

from functools import lru_cache

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from .config import settings


@lru_cache(maxsize=1)
def _get_vectorstore() -> Chroma:
    embedding = HuggingFaceEmbeddings(
        model_name=settings.embedding_model_name,
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(
        persist_directory=settings.chroma_persist_dir,
        embedding_function=embedding,
        collection_name=settings.chroma_collection_name,
    )


def retrieve_with_sources(query: str, k: int | None = None) -> tuple[str, list[str]]:
    """Trả về (ngữ cảnh văn bản, danh sách tiêu đề/nguồn trích dẫn)."""
    vectorstore = _get_vectorstore()
    results = vectorstore.similarity_search("query: " + query, k=k or settings.rag_top_k)
    if not results:
        return "", []
    context = "\n\n".join(r.page_content.replace("passage: ", "") for r in results)
    sources = []
    for r in results:
        meta = getattr(r, "metadata", {}) or {}
        source_name = meta.get("title") or meta.get("source") or meta.get("url")
        if not source_name:
            clean_txt = r.page_content.replace("passage: ", "").strip()
            source_name = clean_txt[:45] + ("..." if len(clean_txt) > 45 else "")
        if source_name and source_name not in sources:
            sources.append(source_name)
    return context, sources


def retrieve(query: str, k: int | None = None) -> str:
    """Trả về đoạn văn bản ngữ cảnh (đã nối các chunk liên quan) hoặc "" nếu không có."""
    context, _ = retrieve_with_sources(query, k=k)
    return context

