"""Hugging Face Spaces entrypoint — khởi chạy FastAPI trên port 7860."""

import os
import uvicorn
from api import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
