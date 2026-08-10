"""LangGraph agent — điều phối luồng xử lý:

    classify (PhoBERT) --> route_decision --+--> escalate --+
                                             +--> tool ------+--> generate (Gemini) --> END
                                             +--> rag -------+

- classify: chạy 2 model PhoBERT (aspect + sentiment), quyết định có escalate không.
- route_decision: dựa vào escalate + từ khóa trong câu hỏi, chọn nhánh xử lý.
- rag / tool / escalate: mỗi nhánh chuẩn bị "context" khác nhau cho bước generate.
- generate: gọi LLM (Gemini) sinh câu trả lời tiếng Việt, CHỈ dựa trên context đã có.
"""

import re
import sqlite3
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from .llm import get_llm
from .models import classify
from .rag import retrieve_with_sources
from .tools import calculate_savings_interest, check_card_status_mock, get_exchange_rate, search_atm_branch_mock

TOOL_KEYWORDS = ["tỷ giá", "ty gia", "đổi tiền", "quy đổi", "ngoại tệ", "tiền thái", "baht", "thb", "usd", "eur", "jpy", "cny", "won", "yen"]
CARD_STATUS_KEYWORDS = ["trạng thái thẻ", "thẻ có bị khóa", "kiểm tra thẻ", "thẻ của tôi"]
SAVINGS_KEYWORDS = ["tính lãi", "tinh lai", "lãi tiết kiệm", "lai tiet kiem", "gửi tiết kiệm", "gui tiet kiem", "lãi dự kiến"]
ATM_KEYWORDS = ["atm", "cây atm", "cay atm", "chi nhánh", "chi nhanh", "phòng giao dịch", "phong giao dich", "địa chỉ atm", "tìm atm", "tìm chi nhánh"]

CURRENCY_MAP = {
    "thb": "THB", "thái": "THB", "baht": "THB", "bat": "THB",
    "usd": "USD", "đô": "USD", "dolar": "USD", "mỹ": "USD",
    "krw": "KRW", "won": "KRW", "hàn": "KRW",
    "eur": "EUR", "euro": "EUR",
    "jpy": "JPY", "yen": "JPY", "nhật": "JPY",
    "cny": "CNY", "tệ": "CNY", "trung": "CNY",
    "gbp": "GBP", "bảng": "GBP", "anh": "GBP",
    "aud": "AUD", "úc": "AUD",
    "cad": "CAD", "sgd": "SGD", "sing": "SGD",
    "twd": "TWD", "đài": "TWD",
}

SYSTEM_PROMPT = (
    "Bạn là trợ lý ảo hỗ trợ khách hàng ngân hàng thông minh, trả lời bằng tiếng Việt, giọng điệu "
    "thân thiện, chuyên nghiệp, ngắn gọn (tối đa 4-5 câu trừ khi cần liệt kê).\n"
    "1. Ưu tiên sử dụng thông tin trong phần NGỮ CẢNH bên dưới để trả lời chính xác nhất.\n"
    "2. Nếu ngữ cảnh chưa đề cập đầy đủ nhưng câu hỏi thuộc về quy trình/nghiệp vụ ngân hàng "
    "cơ bản (như hướng dẫn lấy lại/quên mật khẩu ngân hàng số, quy trình mở thẻ, cấp lại mã PIN...), "
    "hãy giải đáp các bước hướng dẫn cơ bản nhất một cách hữu ích và nhắc khách hàng có thể gọi tổng đài nếu cần hỗ trợ trực tiếp.\n"
    "3. Nếu ngữ cảnh có gắn nhãn [ESCALATE], hãy trả lời 1-2 câu trấn an và thông báo "
    "chuyển nhân viên tư vấn xử lý trực tiếp."
)


def redact_pii(text: str) -> str:
    """Tự động phát hiện và che mờ các thông tin cá nhân nhạy cảm (Số CCCD, Số thẻ 16 số, OTP)."""
    if not text:
        return ""
    # Che mờ số CCCD (12 chữ số)
    text = re.sub(r'\b(\d{4})\d{4}(\d{4})\b', r'\1****\2', text)
    # Che mờ số thẻ 16 chữ số
    text = re.sub(r'\b(\d{4})[-\s]?\d{4}[-\s]?\d{4}[-\s]?(\d{4})\b', r'\1-****-****-\2', text)
    # Che mờ OTP
    text = re.sub(r'(?i)\b(mã\s*otp|otp\s*là|otp)\s*:?\s*(\d{4,6})\b', r'\1: ****', text)
    return text


def rewrite_query_with_context(state: TypedDict) -> str:
    """Nếu có lịch sử hội thoại trước đó, sử dụng LLM để viết lại câu hỏi mới nhất của người dùng
    thành một câu truy vấn RAG độc lập và rõ nghĩa."""
    history = state.get("messages", [])
    raw_message = state.get("message", "")
    if not history or len(history) <= 1:
        return raw_message

    past_chats = []
    for msg in history[:-1]:
        if isinstance(msg, HumanMessage):
            past_chats.append(f"Khách hàng: {msg.content}")
        elif isinstance(msg, AIMessage):
            past_chats.append(f"Trợ lý AI: {msg.content}")

    if not past_chats:
        return raw_message

    chat_str = "\n".join(past_chats[-4:])
    rewrite_prompt = (
        "Dựa vào lịch sử hội thoại bên dưới, hãy viết lại câu hỏi mới nhất của khách hàng thành "
        "một câu hỏi tìm kiếm độc lập, rõ ràng đối tượng và dịch vụ ngân hàng (không dùng đại từ mơ hồ như 'gói đó', 'thẻ đó', 'nó'). "
        "CHỈ trả về câu hỏi đã viết lại duy nhất, không thêm bất kỳ văn bản nào khác.\n\n"
        f"Lịch sử hội thoại:\n{chat_str}\n\n"
        f"Câu hỏi mới của khách hàng: {raw_message}\n\n"
        "Câu hỏi độc lập:"
    )
    try:
        llm = get_llm()
        resp = llm.invoke([HumanMessage(content=rewrite_prompt)])
        rewritten = resp.content.strip() if resp and resp.content else raw_message
        return rewritten
    except Exception:
        return raw_message


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    message: str
    aspect: str
    sentiment: str
    escalate: bool
    context: str
    sources: list[str]
    response: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def classify_node(state: AgentState) -> AgentState:
    result = classify(state["message"])
    return {**state, **result}


def route_decision(state: AgentState) -> str:
    if state.get("escalate"):
        return "escalate"
    text = state["message"].lower()
    if any(k in text for k in TOOL_KEYWORDS + CARD_STATUS_KEYWORDS + SAVINGS_KEYWORDS + ATM_KEYWORDS):
        return "tool"
    return "rag"


def rag_node(state: AgentState) -> AgentState:
    search_query = rewrite_query_with_context(state)
    context, sources = retrieve_with_sources(search_query)
    return {**state, "context": context, "sources": sources}


def tool_node(state: AgentState) -> AgentState:
    text = state["message"].lower()
    if any(k in text for k in CARD_STATUS_KEYWORDS):
        result = check_card_status_mock.invoke({"card_last4": "1234"})
    elif any(k in text for k in SAVINGS_KEYWORDS):
        result = calculate_savings_interest.invoke({"amount_vnd": 100_000_000, "term_months": 12, "interest_rate_year": 5.5})
    elif any(k in text for k in ATM_KEYWORDS):
        result = search_atm_branch_mock.invoke({"location": "Quận 1"})
    else:
        currency = "USD"
        for kw, code in CURRENCY_MAP.items():
            if kw in text:
                currency = code
                break
        result = get_exchange_rate.invoke({"currency": currency})
    return {**state, "context": result}


def escalate_node(state: AgentState) -> AgentState:
    context = (
        "[ESCALATE] Phản hồi thuộc nhóm nhạy cảm (bảo mật/tài khoản/thẻ) và mang cảm xúc "
        "tiêu cực. Cần chuyển nhân viên hỗ trợ xử lý trực tiếp, không tự động xử lý chi tiết."
    )
    return {**state, "context": context}


def _normalize_llm_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks = []
        for item in value:
            chunk = _normalize_llm_text(item)
            if chunk:
                chunks.append(chunk)
        return "\n".join(chunks)
    if isinstance(value, dict):
        for key in ("text", "content"):
            if key in value and value[key] is not None:
                return _normalize_llm_text(value[key])
        return str(value)
    return str(value)


def _build_messages(state: AgentState) -> list:
    history = state.get("messages", [])
    past_messages = []
    if history:
        for msg in history[:-1]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                past_messages.append(msg)

    user_prompt = (
        f"Khía cạnh (aspect): {state.get('aspect', 'N/A')}\n"
        f"Cảm xúc (sentiment): {state.get('sentiment', 'N/A')}\n\n"
        f"Ngữ cảnh:\n{state.get('context') or '(không có ngữ cảnh liên quan)'}\n\n"
        f"Câu hỏi/phản hồi của khách hàng: {state['message']}"
    )
    return [SystemMessage(content=SYSTEM_PROMPT)] + past_messages + [HumanMessage(content=user_prompt)]


def generate_node(state: AgentState) -> AgentState:
    llm = get_llm()
    result = llm.invoke(_build_messages(state))
    response_text = _normalize_llm_text(result.content)
    return {
        **state,
        "response": response_text,
        "messages": [AIMessage(content=response_text)],
    }


# ---------------------------------------------------------------------------
# Graph & SqliteSaver Checkpointer
# ---------------------------------------------------------------------------

_db_conn = None


def _get_checkpointer():
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect("banking_chat.db", check_same_thread=False)
    return SqliteSaver(_db_conn)


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node)
    graph.add_node("rag", rag_node)
    graph.add_node("tool", tool_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        route_decision,
        {"rag": "rag", "tool": "tool", "escalate": "escalate"},
    )
    graph.add_edge("rag", "generate")
    graph.add_edge("tool", "generate")
    graph.add_edge("escalate", "generate")
    graph.add_edge("generate", END)

    checkpointer = _get_checkpointer()
    return graph.compile(checkpointer=checkpointer)


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_graph()
    return _agent


def run_agent(message: str, thread_id: str = "default") -> dict:
    """Chạy toàn bộ graph với memory saver và PII redaction theo thread_id."""
    clean_message = redact_pii(message)
    config = {"configurable": {"thread_id": thread_id}}
    return get_agent().invoke(
        {"message": clean_message, "messages": [HumanMessage(content=clean_message)]},
        config=config,
    )


def stream_agent_response(message: str, thread_id: str = "default"):
    """Generator streaming token-level cho FastAPI /chat/stream với PII redaction."""
    clean_message = redact_pii(message)
    config = {"configurable": {"thread_id": thread_id}}
    agent = get_agent()

    current_state = agent.get_state(config)
    existing_messages = current_state.values.get("messages", []) if current_state and current_state.values else []

    state: AgentState = {
        "message": clean_message,
        "messages": list(existing_messages) + [HumanMessage(content=clean_message)],
    }
    state.update(classify(clean_message))

    # Lưu ngay HumanMessage vào SQLite checkpointer để Sidebar hiển thị phiên chat lập tức
    agent.update_state(
        config,
        {
            "message": clean_message,
            "messages": [HumanMessage(content=clean_message)],
        },
    )

    route = route_decision(state)
    if route == "escalate":
        state = escalate_node(state)
    elif route == "tool":
        state = tool_node(state)
    else:
        state = rag_node(state)

    yield {
        "aspect": state.get("aspect", ""),
        "sentiment": state.get("sentiment", ""),
        "escalate": bool(state.get("escalate", False)),
        "route": route,
        "sources": state.get("sources", []),
    }

    llm = get_llm()
    full_chunks = []
    messages = _build_messages(state)
    for chunk in llm.stream(messages):
        if chunk.content:
            full_chunks.append(chunk.content)
            yield chunk.content

    full_response = "".join(full_chunks)

    agent.update_state(
        config,
        {
            "messages": [AIMessage(content=full_response)],
            "aspect": state.get("aspect", ""),
            "sentiment": state.get("sentiment", ""),
            "escalate": state.get("escalate", False),
            "context": state.get("context", ""),
            "response": full_response,
        },
    )


def clear_agent_history(thread_id: str = "default") -> bool:
    """Xóa lịch sử trò chuyện trong SQLite database cho thread_id."""
    global _db_conn
    _get_checkpointer()  # Đảm bảo _db_conn đã khởi tạo
    if _db_conn:
        try:
            _db_conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            _db_conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            _db_conn.commit()
            return True
        except Exception:
            pass
    return False


def get_agent_history(thread_id: str = "default") -> list[dict]:
    """Lấy danh sách các tin nhắn trong quá khứ của thread_id dưới dạng list[dict]."""
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}
    state = agent.get_state(config)
    if not state or not state.values:
        return []
    raw_messages = state.values.get("messages", [])
    formatted = []
    for msg in raw_messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant" if isinstance(msg, AIMessage) else "system"
        if role in ("user", "assistant"):
            formatted.append({"role": role, "content": str(msg.content)})
    return formatted


def list_agent_threads() -> list[dict]:
    """Trả về danh sách tất cả các thread_id đang lưu trong SQLite database."""
    agent = get_agent()
    threads = []
    seen = set()
    if hasattr(agent, "checkpointer") and hasattr(agent.checkpointer, "list"):
        try:
            for cp in agent.checkpointer.list(None):
                cfg = getattr(cp, "config", {}) or {}
                thread_id = cfg.get("configurable", {}).get("thread_id")
                if thread_id and thread_id not in seen:
                    seen.add(thread_id)
                    history = get_agent_history(thread_id)
                    title = "Cuộc trò chuyện mới"
                    for msg in history:
                        if msg["role"] == "user" and msg["content"].strip():
                            raw_title = msg["content"].strip()
                            title = raw_title[:35] + ("..." if len(raw_title) > 35 else "")
                            break
                    threads.append({
                        "thread_id": thread_id,
                        "title": title,
                        "message_count": len(history),
                    })
        except Exception:
            pass
    return threads




