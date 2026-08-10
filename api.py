"""FastAPI backend cho Vietnamese Banking Assistant.

Chạy dev:      uvicorn api:app --reload
Chạy production: xem Dockerfile
"""

import json
import logging
import os

# Tắt warning rác từ HuggingFace Hub & Tokenizers
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent import clear_agent_history, get_agent_history, list_agent_threads, run_agent, stream_agent_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("banking-assistant")

app = FastAPI(
    title="Vietnamese Banking Assistant API",
    description="Agent đa nhánh: PhoBERT classify (routing) + RAG + tool + Gemini generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # siết lại domain cụ thể khi deploy thật
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warmup_models():
    """Pre-load các model PhoBERT, E5 Embedding và Chroma DB vào RAM khi server khởi động.
    Tránh trễ ở lần truy vấn đầu tiên (Cold Start).
    """
    logger.info("⚡ Đang nạp trước model PhoBERT & Chroma DB vào RAM...")
    try:
        from src.models import classify
        from src.rag import retrieve
        classify("xin chào")
        retrieve("xin chào")
        logger.info("✅ Nạp model thành công! Hệ thống sẵn sàng phản hồi siêu tốc.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cảnh báo warmup model: %s", exc)



class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    api_key: str | None = None
    model: str | None = None


class ClearRequest(BaseModel):
    thread_id: str = "default"


class ChatResponse(BaseModel):
    aspect: str
    sentiment: str
    escalate: bool
    response: str


@app.get("/health")
def health():
    return {"status": "ok"}


def _normalize_response_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks = []
        for item in value:
            if isinstance(item, dict) and "text" in item:
                chunks.append(str(item["text"]))
            elif isinstance(item, str):
                chunks.append(item)
            else:
                chunks.append(str(item))
        return "\n".join(chunks)
    if isinstance(value, dict):
        for key in ("text", "content"):
            if key in value:
                return _normalize_response_text(value[key])
        return str(value)
    return str(value)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message không được để trống")
    try:
        result = run_agent(req.message, req.thread_id, api_key=req.api_key, model=req.model)
    except Exception:
        logger.exception("Lỗi khi chạy agent")
        raise HTTPException(status_code=500, detail="Lỗi xử lý phía server, thử lại sau.")

    return ChatResponse(
        aspect=result.get("aspect", ""),
        sentiment=result.get("sentiment", ""),
        escalate=bool(result.get("escalate", False)),
        response=_normalize_response_text(result.get("response", "")),
    )


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """Server-Sent-Events style streaming — mỗi dòng bắt đầu bằng 'data: '."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message không được để trống")

    def event_generator():
        try:
            for item in stream_agent_response(req.message, req.thread_id, api_key=req.api_key, model=req.model):
                if isinstance(item, dict):
                    yield f"data: {json.dumps({'meta': item}, ensure_ascii=False)}\n\n"
                elif isinstance(item, str) and item:
                    yield f"data: {json.dumps({'token': item}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Lỗi khi streaming agent")
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/chat/clear")
def clear_chat(req: ClearRequest):
    """Làm sạch bộ nhớ câu thoại trong memory saver theo thread_id."""
    cleared = clear_agent_history(req.thread_id)
    return {"status": "ok", "thread_id": req.thread_id, "cleared": cleared}


@app.get("/chat/threads")
def get_threads():
    """Lấy danh sách tất cả các phiên trò chuyện (threads) hiện có."""
    return {"threads": list_agent_threads()}


@app.get("/chat/history/{thread_id}")
def get_history(thread_id: str):
    """Lấy toàn bộ tin nhắn lịch sử của thread_id."""
    return {"thread_id": thread_id, "messages": get_agent_history(thread_id)}


@app.delete("/chat/threads/{thread_id}")
def delete_thread(thread_id: str):
    """Xóa 1 phiên trò chuyện theo thread_id."""
    cleared = clear_agent_history(thread_id)
    return {"status": "ok", "thread_id": thread_id, "deleted": cleared}


# Mount static directory cho Web Chat Interface (nếu tồn tại)
import os
from fastapi.staticfiles import StaticFiles

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")




