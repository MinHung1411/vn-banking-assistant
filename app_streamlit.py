# Patch sqlite3 cho Streamlit Cloud Linux (ChromaDB tương thích)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import time
import uuid
import streamlit as st
from dotenv import load_dotenv

# Load môi trường từ .env
load_dotenv()

# Đồng bộ Streamlit Cloud Secrets vào os.environ
if hasattr(st, "secrets"):
    for key in st.secrets:
        if isinstance(st.secrets[key], str) and key not in os.environ:
            os.environ[key] = st.secrets[key]

st.set_page_config(
    page_title="Vietnamese Banking Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Import backend agent
from src.agent import stream_agent_response, get_agent_history, clear_agent_history

# Custom CSS Glassmorphism ép Full Dark Mode 100% & Giao diện Chat Zalo/Messenger
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
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1050px !important;
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
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
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

    /* === KHUNG CHAT ĐỐI THOẠI (ZALO / MESSENGER STYLE) === */
    div[data-testid="stChatMessage"] {
        display: flex !important;
        width: fit-content !important;
        min-width: 80px !important;
        padding: 14px 18px !important;
        margin-bottom: 14px !important;
        transition: all 0.2s ease !important;
    }

    /* User Message: Căn sát mép phải, nền xanh Messenger/Zalo nổi bật */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
    div[data-testid="stChatMessage"]:has([data-testid*="User"]),
    div[data-testid="stChatMessage"]:has([aria-label*="user" i]),
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarUser) {
        flex-direction: row-reverse !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        max-width: 78% !important;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: 1px solid rgba(147, 197, 253, 0.3) !important;
        border-radius: 20px 20px 4px 20px !important;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.28) !important;
    }

    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"],
    div[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageContent"] {
        text-align: left !important;
    }

    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
    div[data-testid="stChatMessage"]:has([data-testid*="User"]) p,
    div[data-testid="stChatMessage"]:has([data-testid*="User"]) span {
        color: #ffffff !important;
        font-size: 0.96rem !important;
        line-height: 1.55 !important;
    }

    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageAvatarUser"],
    div[data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid*="Avatar"] {
        margin-left: 12px !important;
        margin-right: 0 !important;
        background: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 50% !important;
    }

    /* Assistant Message: Căn mép trái, màu nền Dark Slate sang trọng */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
    div[data-testid="stChatMessage"]:has([data-testid*="Assistant"]),
    div[data-testid="stChatMessage"]:has([aria-label*="assistant" i]),
    div[data-testid="stChatMessage"]:has(.stChatMessageAvatarAssistant) {
        flex-direction: row !important;
        margin-right: auto !important;
        margin-left: 0 !important;
        max-width: 82% !important;
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px 20px 20px 4px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
    }

    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) p,
    div[data-testid="stChatMessage"]:has([data-testid*="Assistant"]) p,
    div[data-testid="stChatMessage"]:has([data-testid*="Assistant"]) div {
        color: #f8fafc !important;
        font-size: 0.96rem !important;
        line-height: 1.65 !important;
    }

    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageAvatarAssistant"],
    div[data-testid="stChatMessage"]:has([data-testid*="Assistant"]) [data-testid*="Avatar"] {
        margin-right: 12px !important;
        margin-left: 0 !important;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        border: 1px solid rgba(245, 158, 11, 0.5) !important;
        border-radius: 50% !important;
    }

    /* Bảng và định dạng trong tin nhắn */
    div[data-testid="stChatMessage"] table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 8px 0 !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stChatMessage"] th, div[data-testid="stChatMessage"] td {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding: 6px 10px !important;
    }
    div[data-testid="stChatMessage"] th {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #818cf8 !important;
    }

    /* === GỢI Ý CÂU HỎI NHANH (MINI PILL CHIPS) === */
    .quick-suggest-header {
        font-size: 0.74rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        margin-top: 14px !important;
        margin-bottom: 6px !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
    }

    div[data-testid="stHorizontalBlock"] .stButton>button {
        padding: 4px 8px !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        border-radius: 16px !important;
        background: rgba(30, 41, 59, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #e2e8f0 !important;
        min-height: 32px !important;
        height: 32px !important;
        line-height: 1 !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
        overflow: hidden !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    div[data-testid="stHorizontalBlock"] .stButton>button:hover {
        background: #4f46e5 !important;
        color: #ffffff !important;
        border-color: #818cf8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
    }

    .brand-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 16px 20px;
        border-radius: 18px;
        margin-bottom: 18px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    .brand-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .brand-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-icon {
        width: 42px;
        height: 42px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
    }
    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
    }
    .brand-subtitle {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 1px;
    }
    .status-badge {
        padding: 4px 12px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px;
        font-size: 0.75rem;
        color: #34d399;
        font-weight: 600;
    }
    .tech-pills-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding-top: 10px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
    }
    .tech-pill {
        padding: 4px 10px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        font-size: 0.75rem;
        color: #cbd5e1;
    }
    .tech-pill b {
        color: #818cf8;
    }

    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
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

    section[data-testid="stSidebar"] .stButton>button {
        border-radius: 12px !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        background: rgba(30, 41, 59, 0.9) !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 8px 12px !important;
        min-height: 40px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
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
                <div class="brand-subtitle">Trợ lý ngân hàng số thông minh & bảo mật</div>
            </div>
        </div>
        <div class="status-badge">🟢 Trực tuyến 24/7</div>
    </div>
    <div class="tech-pills-row">
        <span class="tech-pill">🔒 <b>Bảo mật:</b> Tự động che mờ thông tin cá nhân (PII)</span>
        <span class="tech-pill">⚡ <b>Tốc độ:</b> Phản hồi tức thì</span>
        <span class="tech-pill">🏛️ <b>Dịch vụ:</b> Tra cứu tỷ giá, thẻ, lãi suất & chi nhánh</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Hiển thị các tin nhắn hội thoại
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg and msg["meta"]:
            meta = msg["meta"]
            escalate = meta.get("escalate", False)
            if escalate:
                st.markdown('<div class="badge-container"><span class="badge badge-escalate">⚠️ Chuyển chuyên viên tư vấn (Escalated)</span></div>', unsafe_allow_html=True)

# Gợi ý nhanh - Thu gọn mini pill chips đặt ngay trên ô chat input
st.markdown('<div class="quick-suggest-header">⚡ Gợi ý câu hỏi nhanh:</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

selected_prompt = None
with col1:
    if st.button("💱 Tỷ giá USD", key="quick_usd", use_container_width=True):
        selected_prompt = "Tỷ giá USD hôm nay bao nhiêu?"
with col2:
    if st.button("💳 Kiểm tra thẻ", key="quick_card", use_container_width=True):
        selected_prompt = "Kiểm tra giúp tôi trạng thái thẻ ****1234"
with col3:
    if st.button("💰 Lãi tiết kiệm", key="quick_save", use_container_width=True):
        selected_prompt = "Tính lãi tiết kiệm 100 triệu gửi 12 tháng lãi suất 5.5%"
with col4:
    if st.button("📍 ATM & Chi nhánh", key="quick_branch", use_container_width=True):
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
        message_placeholder.markdown("*🔍 Đang xử lý yêu cầu...* ▌")
        
        full_response = ""
        meta_info = {}

        try:
            generator = stream_agent_response(
                prompt,
                thread_id=st.session_state.thread_id
            )
            first_item = next(generator, None)
            if isinstance(first_item, dict):
                meta_info = first_item

            # Streaming mượt mà trực tiếp theo token từ LLM
            for token in generator:
                if isinstance(token, str):
                    full_response += token
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

            escalate = meta_info.get("escalate", False)
            if escalate:
                st.markdown('<div class="badge-container"><span class="badge badge-escalate">⚠️ Chuyển chuyên viên tư vấn (Escalated)</span></div>', unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "meta": meta_info
            })
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "exceeded" in err_str.lower():
                err_msg = (
                    "⚠️ **Hệ thống hiện đang phục vụ nhiều lượt truy cập cùng lúc.**\n\n"
                    "Quý khách vui lòng gửi lại câu hỏi sau giây lát hoặc liên hệ hotline tổng đài để được tư vấn viên hỗ trợ trực tiếp ạ."
                )
            else:
                err_msg = "⚠️ Đã xảy ra gián đoạn khi xử lý yêu cầu. Quý khách vui lòng thử lại sau giây lát."
            message_placeholder.markdown(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})

