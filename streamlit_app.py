"""Streamlit Community Cloud standard entry point file."""

# Patch sqlite3 cho Streamlit Cloud Linux (ChromaDB tương thích)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import streamlit as st

# Đồng bộ Streamlit Cloud Secrets vào os.environ
if hasattr(st, "secrets"):
    for key in st.secrets:
        if isinstance(st.secrets[key], str) and key not in os.environ:
            os.environ[key] = st.secrets[key]

# Import và thực thi ứng dụng Streamlit chính
import app_streamlit
