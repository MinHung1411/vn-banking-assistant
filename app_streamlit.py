import os
import time
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

# Import backend agent
from src.agent import stream_agent_response, get_agent_history, clear_agent_history

# Custom CSS Glassmorphism ép Full Dark Mode 100%
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    footer {visibility: hidden;}

    .stMainBlockContainer {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px !important;
    }

    div[data-testid="stBottomBlockContainer"] {
        background-color: #0b0f19 !important;
    }
    
    div[data-baseweb="textarea"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }

    div[data-testid="stChatInput"] {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
    }
    
    div[data-testid="stChatInput"] textarea {
        color: #f8fafc !important;
        background-color: transparent !important;
        font-size: 0.95rem !important;
    }

    div[data-testid="stChatInput"] button {
        background-color: #6366f1 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: none !important;
    }

    div[data-testid="stChatMessage"] {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 18px !important;
        padding: 18px !important;
        color: #f8fafc !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] div {
        color: #f8fafc !important;
        font-size: 0.98rem !important;
        line-height: 1.65 !important;
    }

    .brand-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 20px 24px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    .brand-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .brand-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .brand-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
    }
    .brand-title {
        font-size: 1.55rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
    }
    .brand-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .status-badge {
        padding: 6px 14px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px;
        font-size: 0.78rem;
        color: #34d399;
        font-weight: 600;
    }
    .tech-pills-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
    }
    .tech-pill {
        padding: 5px 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        font-size: 0.78rem;
        color: #cbd5e1;
    }
    .tech-pill b {
        color: #818cf8;
    }

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
    }
    .badge-aspect {
        background: rgba(14, 165, 233, 0.2);
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.4);
    }
    .badge-sentiment-positive {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80 !important;
        border: 1px solid rgba(74, 222, 128, 0.4);
    }
    .badge-sentiment-neutral {
        background: rgba(148, 163, 184, 0.2);
        color: #cbd5e1 !important;
        border: 1px solid rgba(203, 213, 225, 0.4);
    }
    .badge-sentiment-negative {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171 !important;
        border: 1px solid rgba(248, 113, 113, 0.4);
    }
    .badge-escalate {
        background: rgba(245, 158, 11, 0.25);
        color: #fbbf24 !important;
        border: 1px solid rgba(251, 191, 36, 0.5);
    }

    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    .stButton>button {
        border-radius: 20px !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        background: rgba(30, 41, 59, 0.9) !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: #4f46e5 !important;
        color: #ffffff !important;
        border-color: #6366f1 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo Session State cô lập theo thiết bị/người dùng
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]

if "my_threads" not in st.session_state:
    st.session_state.my_threads = {}

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Xin chào quý khách! Em là **Trợ lý ảo Ngân hàng**. Em có thể hỗ trợ quý khách tra cứu tỷ giá ngoại tệ, kiểm tra thông tin dịch vụ, tính lãi tiết kiệm hoặc kết nối tư vấn viên khi cần thiết ạ."}
    ]

# SIDEBAR: Cô lập lịch sử cá nhân
with st.sidebar:
    st.markdown("### 🏛️ AI Banking Assistant")
    
    if st.button("✨ + Cuộc trò chuyện mới", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())[:8]
        st.session_state.thread_id = new_id
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào quý khách! Em là **Trợ lý ảo Ngân hàng**. Quý khách cần em hỗ trợ thông tin gì hôm nay ạ?"}
        ]
        st.rerun()

    st.markdown("---")
    st.markdown("### 📜 LỊCH SỬ CỦA BẠN")
    
    if st.session_state.my_threads:
        for t_id, t_title in list(st.session_state.my_threads.items()):
            is_active = (t_id == st.session_state.thread_id)
            btn_label = f"{'💬 ' if not is_active else '👉 '} {t_title}"
            
            if st.button(btn_label, key=f"user_thread_{t_id}", use_container_width=True):
                st.session_state.thread_id = t_id
                st.session_state.messages = get_agent_history(t_id)
                st.rerun()
    else:
        st.caption("Chưa có phiên trò chuyện cá nhân nào.")

    st.markdown("---")
    if st.button("🗑️ Xóa phiên hiện tại", use_container_width=True):
        clear_agent_history(st.session_state.thread_id)
        if st.session_state.thread_id in st.session_state.my_threads:
            del st.session_state.my_threads[st.session_state.thread_id]
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào quý khách! Em là **Trợ lý ảo Ngân hàng**. Quý khách cần em hỗ trợ thông tin gì hôm nay ạ?"}
        ]
        st.rerun()

# MAIN INTERFACE
st.markdown("""
<div class="brand-header">
    <div class="brand-top-row">
        <div class="brand-left">
            <div class="brand-icon">🏦</div>
            <div>
                <div class="brand-title">Vietnamese Banking Assistant</div>
                <div class="brand-subtitle">Agent tư vấn tự động ngân hàng tiếng Việt</div>
            </div>
        </div>
        <div class="status-badge">🟢 Streamlit Online</div>
    </div>
    <div class="tech-pills-row">
        <span class="tech-pill">🧠 <b>Model:</b> PhoBERT Fine-tuned</span>
        <span class="tech-pill">🔀 <b>Router:</b> LangGraph StateGraph</span>
        <span class="tech-pill">📚 <b>Knowledge:</b> Chroma Vector DB (RAG)</span>
        <span class="tech-pill">⚡ <b>LLM:</b> Gemini API</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Hiển thị các tin nhắn hội thoại
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

# Gợi ý nhanh (Pill Buttons lơ lửng)
st.caption("💡 GỢI Ý CÂU HỎI NHANH")
col1, col2, col3, col4 = st.columns(4)

selected_prompt = None
with col1:
    if st.button("💱 Tỷ giá USD hôm nay", use_container_width=True):
        selected_prompt = "Tỷ giá USD hôm nay bao nhiêu?"
with col2:
    if st.button("💳 Trạng thái thẻ", use_container_width=True):
        selected_prompt = "Kiểm tra giúp tôi trạng thái thẻ ****1234"
with col3:
    if st.button("💰 Tính lãi tiết kiệm", use_container_width=True):
        selected_prompt = "Tính lãi tiết kiệm 100 triệu gửi 12 tháng lãi suất 5.5%"
with col4:
    if st.button("📍 Cây ATM & Chi nhánh", use_container_width=True):
        selected_prompt = "Tìm giúp tôi chi nhánh và cây ATM ở Quận 1"

# Chat Input & Stream Processing
prompt = st.chat_input("Nhập câu hỏi của quý khách tại đây...") or selected_prompt

if prompt:
    if st.session_state.thread_id not in st.session_state.my_threads:
        short_title = prompt.strip()[:30] + ("..." if len(prompt.strip()) > 30 else "")
        st.session_state.my_threads[st.session_state.thread_id] = short_title

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        # Hiển thị trực tiếp dòng chữ trạng thái Đang suy nghĩ nổi bật ngay trong khung chat
        message_placeholder.markdown("*🔍 Đang phân tích ý định (PhoBERT) & tra cứu tri thức (Chroma RAG)...* ▌")
        
        full_response = ""
        meta_info = {}

        try:
            generator = stream_agent_response(prompt, thread_id=st.session_state.thread_id)
            first_item = next(generator, None)
            if isinstance(first_item, dict):
                meta_info = first_item

            # Thay thế dòng suy nghĩ bằng câu trả lời tự nhiên gõ từng ký tự
            for token in generator:
                if isinstance(token, str):
                    for char in token:
                        full_response += char
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.008)

            message_placeholder.markdown(full_response)

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

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "meta": meta_info
            })
        except Exception as e:
            err_msg = f"Đã xảy ra lỗi khi xử lý: {str(e)}"
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
