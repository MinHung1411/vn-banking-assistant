"""Hugging Face Spaces entrypoint — Gradio ChatInterface."""

import os
from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from src.agent import run_agent


def respond(message, history):
    if not message or not message.strip():
        return "Xin chào! Tôi là trợ lý ảo ngân hàng. Bạn cần hỗ trợ gì ạ?"
    try:
        result = run_agent(message.strip(), thread_id="gradio_session")
        response = result.get("response", "")
        return response if response else "Xin lỗi, vui lòng thử lại!"
    except Exception as e:
        return f"Đã xảy ra lỗi: {str(e)}"


demo = gr.ChatInterface(
    fn=respond,
    title="🏦 Vietnamese Banking Assistant",
    description="Trợ lý ảo AI ngân hàng tiếng Việt",
)

demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
