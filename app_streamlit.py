import os
import uuid
import streamlit as st
from dotenv import load_dotenv

# Load môi trường
load_dotenv()

st.set_page_config(
    page_title="Vietnamese Banking Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Glassmorphism + Dark/Light Modern Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    /* Header Container */
    .header-box {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .header-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
    }
    
    /* Suggestion Pills Horizontal Scroll */
    .suggestion-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #818cf8;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Badges */
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    .badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-aspect {
        background: rgba(14, 165, 233, 0.2);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .badge-sentiment-positive {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.3);
    }
    .badge-sentiment-neutral {
        background: rgba(148, 163, 184, 0.2);
        color: #cbd5e1;
        border: 1px solid rgba(203, 213, 225, 0.3);
    }
    .badge-sentiment-negative {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }
    .badge-escalate {
        background: rgba(245, 158, 11, 0.25);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.4);
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);
    }
    
    /* Custom Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.85);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* StButton styling */
    .stButton>button {
        border-radius: 12px;
        border: 1px solid rgba(99, 102, 241, 0.3);
        background: rgba(30, 41, 59, 0.8);
        color: #e2e8f0;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: #4f46e5;
        color: #ffffff;
        border-color: #6366f1;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Import backend agent
from src.agent import stream_agent_response, get_agent_history, clear_agent_history

# Session state initialization
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]

if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""

if "messages" not in st.session_state:
    history = get_agent_history(st.session_state.thread_id)
    if history:
        st.session_state.messages = history
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý ảo AI Ngân hàng. Tôi có thể giúp gì cho bạn hôm nay?"}
        ]

# Sidebar
with st.sidebar:
    st.markdown("### 🏦 Quản lý Phiên Chat")
    
    if st.button("➕ Tạo cuộc trò chuyện mới", use_container_width=True, type="primary"):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý ảo AI Ngân hàng. Tôi có thể giúp gì cho bạn hôm nay?"}
        ]
        st.rerun()

    st.caption(f"Session ID: `{st.session_state.thread_id}`")
    
    if st.button("🗑️ Xóa lịch sử phiên này", use_container_width=True):
        clear_agent_history(st.session_state.thread_id)
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý ảo AI Ngân hàng. Tôi có thể giúp gì cho bạn hôm nay?"}
        ]
        st.rerun()
        
    st.markdown("---")
    st.markdown("### ⚡ Tính năng Nổi bật")
    st.markdown("""
    - 🏷️ **PhoBERT Classify**: Tự động nhận diện Aspect & Sentiment.
    - 🔀 **LangGraph Routing**: Tự động chuyển RAG / Tool / Escalation.
    - 🛡️ **PII Redaction**: Che mờ CCCD, Số thẻ & OTP.
    - 📚 **Chroma RAG**: Tra cứu quy định & tin tức ngân hàng.
    - 🛠️ **Realtime Tools**: Tra tỷ giá, tính lãi tiết kiệm, vị trí ATM.
    """)

# Header Banner
st.markdown("""
<div class="header-box">
    <div class="header-title">🏦 Vietnamese Banking Assistant</div>
    <div class="header-subtitle">Hệ thống Trợ lý ảo AI Ngân hàng đa chức năng (PhoBERT Fine-tuned + LangGraph RAG)</div>
</div>
""", unsafe_allow_html=True)

# Hiển thị tin nhắn lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg and msg["meta"]:
            meta = msg["meta"]
            aspect = meta.get("aspect", "")
            sentiment = meta.get("sentiment", "")
            escalate = meta.get("escalate", False)
            
            s_class = f"badge-sentiment-{sentiment}" if sentiment in ["positive", "neutral", "negative"] else "badge-sentiment-neutral"
            badges_html = '<div class="badge-container">'
            if aspect:
                badges_html += f'<span class="badge badge-aspect">Khía cạnh: {aspect}</span>'
            if sentiment:
                badges_html += f'<span class="badge {s_class}">Cảm xúc: {sentiment}</span>'
            if escalate:
                badges_html += '<span class="badge badge-escalate">⚠️ Chuyển tổng đài (Escalated)</span>'
            badges_html += '</div>'
            st.markdown(badges_html, unsafe_allow_html=True)

# Gợi ý nhanh (Floating suggestion pills)
st.markdown('<div class="suggestion-title">💡 Gợi ý câu hỏi nhanh</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

selected_prompt = None
with col1:
    if st.button("💱 Tỷ giá USD hôm nay", use_container_width=True):
        selected_prompt = "Tỷ giá USD hôm nay là bao nhiêu?"
with col2:
    if st.button("🔒 Báo khóa thẻ khẩn cấp", use_container_width=True):
        selected_prompt = "Tôi bị mất thẻ ngân hàng 1234, khóa thẻ giúp tôi với"
with col3:
    if st.button("💰 Tính lãi tiết kiệm 100tr", use_container_width=True):
        selected_prompt = "Tính lãi tiết kiệm 100 triệu gửi 12 tháng lãi suất 5.5%"
with col4:
    if st.button("📍 Cây ATM gần nhất Quận 1", use_container_width=True):
        selected_prompt = "Tìm giúp tôi chi nhánh và cây ATM ở Quận 1"

# Xử lý input từ chat_input hoặc từ gợi ý nhanh (suggestion pill)
prompt = st.chat_input("Nhập câu hỏi hoặc yêu cầu hỗ trợ...") or selected_prompt

if prompt:
    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Hiển thị câu trả lời của assistant với Streaming thời gian thực
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        meta_info = {}

        try:
            generator = stream_agent_response(prompt, thread_id=st.session_state.thread_id)
            # Token đầu tiên chứa metadata (aspect, sentiment, escalate...)
            first_item = next(generator, None)
            if isinstance(first_item, dict):
                meta_info = first_item

            for token in generator:
                if isinstance(token, str):
                    full_response += token
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

            # Hiển thị Badges metadata bên dưới câu trả lời
            aspect = meta_info.get("aspect", "")
            sentiment = meta_info.get("sentiment", "")
            escalate = meta_info.get("escalate", False)

            s_class = f"badge-sentiment-{sentiment}" if sentiment in ["positive", "neutral", "negative"] else "badge-sentiment-neutral"
            badges_html = '<div class="badge-container">'
            if aspect:
                badges_html += f'<span class="badge badge-aspect">Khía cạnh: {aspect}</span>'
            if sentiment:
                badges_html += f'<span class="badge {s_class}">Cảm xúc: {sentiment}</span>'
            if escalate:
                badges_html += '<span class="badge badge-escalate">⚠️ Chuyển tổng đài (Escalated)</span>'
            badges_html += '</div>'
            st.markdown(badges_html, unsafe_allow_html=True)

            # Lưu vào session
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "meta": meta_info
            })
        except Exception as e:
            err_msg = f"Đã xảy ra lỗi khi xử lý: {str(e)}"
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
