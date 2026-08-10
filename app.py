"""Hugging Face Spaces entrypoint — sử dụng Gradio ChatInterface.

Gradio SDK trên HF Spaces yêu cầu ứng dụng Gradio, không phải FastAPI thuần.
File này tạo giao diện chat Gradio gọi trực tiếp vào agent pipeline.
"""

import os
import gradio as gr

# Thiết lập biến môi trường từ .env nếu có (local dev)
from dotenv import load_dotenv
load_dotenv()

from src.agent import run_agent


def respond(message: str, history: list[dict]) -> str:
    """Hàm xử lý chat cho Gradio ChatInterface."""
    if not message or not message.strip():
        return "Xin chào! Tôi là trợ lý ảo ngân hàng. Bạn cần hỗ trợ gì ạ?"

    try:
        # Tạo thread_id duy nhất cho mỗi phiên Gradio
        result = run_agent(message.strip(), thread_id="gradio_session")
        response = result.get("response", "")
        if not response:
            response = "Xin lỗi, tôi chưa thể xử lý yêu cầu này. Vui lòng thử lại!"
        return response
    except Exception as e:
        return f"⚠️ Đã xảy ra lỗi: {str(e)}. Vui lòng thử lại!"


demo = gr.ChatInterface(
    fn=respond,
    type="messages",
    title="🏦 Vietnamese Banking Assistant",
    description=(
        "Trợ lý ảo AI ngân hàng tiếng Việt — Hỗ trợ tỷ giá, lãi suất, "
        "trạng thái thẻ, tìm ATM/chi nhánh, và giải đáp thắc mắc ngân hàng."
    ),
    examples=[
        "Tỷ giá USD hôm nay bao nhiêu?",
        "Tính lãi tiết kiệm 100 triệu kỳ hạn 12 tháng",
        "Kiểm tra trạng thái thẻ 1234567890123456",
        "Tìm ATM gần Quận 1 TP HCM",
        "Hướng dẫn mở tài khoản ngân hàng",
    ],
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="indigo",
    ),
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
