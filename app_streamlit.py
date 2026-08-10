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

# Custom CSS cho giao diện ngân hàng hiện đại
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
    }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .badge-container {
        display: flex;
        gap: 8px;
        margin-top: 8px;
        margin-bottom: 12px;
    }
    .badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-aspect {
        background-color: #e0f2fe;
        color: #0369a1;
    }
    .badge-sentiment-positive {
        background-color: #dcfce7;
        color: #15803d;
    }
    .badge-sentiment-neutral {
        background-color: #f1f5f9;
        color: #475569;
    }
    .badge-sentiment-negative {
        background-color: #fee2e2;
        color: #b91c1c;
    }
    .badge-escalate {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

# Import backend agent
from src.agent import run_agent, get_agent_history, clear_agent_history, list_agent_threads

# Khởi tạo session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]

if "messages" not in st.session_state:
    # Load lịch sử từ SQLite saver nếu có
    history = get_agent_history(st.session_state.thread_id)
    if history:
        st.session_state.messages = history
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý ảo AI Ngân hàng. Tôi có thể giúp gì cho bạn hôm nay?"}
        ]

# Sidebar
with st.sidebar:
    st.title("🏦 Cấu hình & Lịch sử")
    
    st.markdown("### 💬 Cuộc trò chuyện")
    if st.button("➕ Tạo cuộc trò chuyện mới", use_container_width=True, type="primary"):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý ảo AI Ngân hàng. Tôi có thể giúp gì cho bạn hôm nay?"}
        ]
        st.rerun()

    st.caption(f"Session ID hiện tại: `{st.session_state.thread_id}`")
    
    if st.button("🗑️ Xóa lịch sử phiên này", use_container_width=True):
        clear_agent_history(st.session_state.thread_id)
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý ảo AI Ngân hàng. Tôi có thể giúp gì cho bạn hôm nay?"}
        ]
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🛠️ Các tính năng tích hợp")
    st.markdown("""
    - 🏷️ **PhoBERT Classification**: Tự động phân loại 14 khía cạnh & 3 sắc thái cảm xúc.
    - ⚡ **LangGraph Agent**: Điều phối thông minh (RAG / Tool / Escalation).
    - 📚 **Chroma RAG**: Tra cứu thông tin tin tức & quy định ngân hàng.
    - 🛡️ **PII Redaction**: Tự động mờ hóa thông tin nhạy cảm (CCCD/Thẻ/OTP).
    - 🛠️ **Realtime Tools**: Tra cứu tỷ giá ngoại tệ, tính lãi tiết kiệm, tra cứu ATM...
    """)

# Main UI
st.markdown('<div class="main-header">🏦 Vietnamese Banking Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Trợ lý ảo AI Ngân hàng đa chức năng (PhoBERT + RAG + LangGraph)</div>', unsafe_allow_html=True)

# Hiển thị các tin nhắn cũ
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
                badges_html += f'<span class="badge badge-aspect">Aspect: {aspect}</span>'
            if sentiment:
                badges_html += f'<span class="badge {s_class}">Sentiment: {sentiment}</span>'
            if escalate:
                badges_html += '<span class="badge badge-escalate">⚠️ Chuyển tổng đài (Escalated)</span>'
            badges_html += '</div>'
            
            st.markdown(badges_html, unsafe_allow_html=True)

# Xử lý input mới từ người dùng
if prompt := st.chat_input("Nhập câu hỏi hoặc yêu cầu hỗ trợ (VD: Tỷ giá USD hôm nay bao nhiêu?)..."):
    # Thêm user message vào UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Chạy agent backend
    with st.chat_message("assistant"):
        with st.spinner("Đang tư vấn và tra cứu..."):
            try:
                result = run_agent(prompt, thread_id=st.session_state.thread_id)
                response_text = result.get("response", "")
                aspect = result.get("aspect", "")
                sentiment = result.get("sentiment", "")
                escalate = result.get("escalate", False)

                st.markdown(response_text)

                s_class = f"badge-sentiment-{sentiment}" if sentiment in ["positive", "neutral", "negative"] else "badge-sentiment-neutral"
                badges_html = '<div class="badge-container">'
                if aspect:
                    badges_html += f'<span class="badge badge-aspect">Aspect: {aspect}</span>'
                if sentiment:
                    badges_html += f'<span class="badge {s_class}">Sentiment: {sentiment}</span>'
                if escalate:
                    badges_html += '<span class="badge badge-escalate">⚠️ Chuyển tổng đài (Escalated)</span>'
                badges_html += '</div>'

                st.markdown(badges_html, unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "meta": {
                        "aspect": aspect,
                        "sentiment": sentiment,
                        "escalate": escalate
                    }
                })
            except Exception as e:
                err_msg = f"Đã xảy ra lỗi khi xử lý: {str(e)}"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
