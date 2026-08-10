FROM python:3.10-slim

WORKDIR /app

# Cài đặt system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để tận dụng Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Expose port 7860 (mặc định HF Spaces)
EXPOSE 7860

# Chạy FastAPI server
CMD ["python", "app.py"]
