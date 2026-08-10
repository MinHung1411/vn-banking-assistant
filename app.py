import os
import uvicorn
from api import app

if __name__ == "__main__":
    # Port 7860 là cổng mặc định của Hugging Face Spaces
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
