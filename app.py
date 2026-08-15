import sys

# Nếu ứng dụng được khởi chạy bởi Streamlit (vd: Streamlit Cloud mặc định tìm app.py)
try:
    import streamlit as st
    if st.runtime.exists():
        import streamlit_app
        sys.exit(0)
except Exception:
    pass

# === MUST BE FIRST: Patch jinja2 before gradio imports ===
import jinja2.utils


_OrigGet = jinja2.utils.LRUCache.get
_OrigGetItem = jinja2.utils.LRUCache.__getitem__
_OrigSetItem = jinja2.utils.LRUCache.__setitem__
_OrigContains = jinja2.utils.LRUCache.__contains__


def _make_hashable(key):
    """Chuyển dict/list thành tuple hashable để dùng làm cache key."""
    if isinstance(key, dict):
        return ("__dict__", tuple(sorted(
            (k, _make_hashable(v)) for k, v in key.items()
        )))
    if isinstance(key, list):
        return ("__list__", tuple(_make_hashable(i) for i in key))
    if isinstance(key, tuple):
        return tuple(_make_hashable(i) for i in key)
    return key


def _patched_get(self, key, *args, **kwargs):
    return _OrigGet(self, _make_hashable(key), *args, **kwargs)


def _patched_getitem(self, key):
    return _OrigGetItem(self, _make_hashable(key))


def _patched_setitem(self, key, value):
    return _OrigSetItem(self, _make_hashable(key), value)


def _patched_contains(self, key):
    return _OrigContains(self, _make_hashable(key))


jinja2.utils.LRUCache.get = _patched_get
jinja2.utils.LRUCache.__getitem__ = _patched_getitem
jinja2.utils.LRUCache.__setitem__ = _patched_setitem
jinja2.utils.LRUCache.__contains__ = _patched_contains
# === END PATCH ===

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
