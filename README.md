# Vietnamese Banking Assistant (Multi-turn Agentic RAG)

Hệ thống Trợ lý ảo AI ngân hàng tiếng Việt cấp Enterprise: phân loại phản hồi bằng **mô hình PhoBERT fine-tune riêng**, điều phối đa nhánh qua **LangGraph StateGraph**, lưu vết bộ nhớ hội thoại **SQLite Persistence**, xử lý câu hỏi đại từ mơ hồ với **Query Rewriter**, tra cứu tri thức **Chroma RAG (kèm Citations)**, bảo vệ thông tin với **PII Redactor**, cùng giao diện Web UI hỗ trợ **Voice Chat (Speech-to-Text / Text-to-Speech)**.

---

## 🏗️ Kiến trúc Hệ thống (System Architecture)

```
                       Khách hàng gửi tin nhắn
                                 │
                                 ▼
                     [PII Redactor (CCCD/Card/OTP)]
                                 │
                                 ▼
                  [classify (PhoBERT Fine-tuned)]
                                 │
                                 ▼
                         [route_decision]
      ┌──────────────────────────┼──────────────────────────┐
      ▼                          ▼                          ▼
 [escalate]                   [tool]                      [rag]
 (Chuyển tổng đài)   (Tỷ giá / Thẻ / Lãi suất / ATM)  (Query Rewriter + ChromaDB)
      │                          │                          │
      └──────────────────────────┼──────────────────────────┘
                                 ▼
                  [generate (Gemini LLM API)]
                                 │
                                 ▼
              [FastAPI /chat/stream SSE Streaming]
                                 │
                                 ▼
          [Web UI: Sidebar History + Voice Chat STT/TTS]
```

Toàn bộ luồng điều phối trạng thái (State Orchestration) nằm trong `src/agent.py`, sử dụng **LangGraph** (`StateGraph`) kết hợp **SqliteSaver** lưu vết hội thoại bền vững trong `banking_chat.db`.

---

## 🌟 Các Tính năng Nổi bật (Key Features)

1. **Model Fine-tune tiếng Việt**:
   - 2 mô hình PhoBERT fine-tune trên Kaggle (`undertheseanlp/UTS2017_Bank`) cho Aspect Classification (14 nhãn) & Sentiment Analysis (3 nhãn).
2. **Quản lý Bộ nhớ & Trò chuyện Đa lượt (Multi-turn Memory)**:
   - Tích hợp `SqliteSaver` lưu trữ dữ liệu các phiên chat (`thread_id`) bền vững trong cơ sở dữ liệu SQLite.
3. **Query Rewriter (Viết lại câu hỏi nối tiếp RAG)**:
   - Tự động chuyển các câu hỏi ở lượt sau sử dụng đại từ mơ hồ (*"gói đó"*, *"thẻ này"*, *"nó"*) thành câu truy vấn RAG độc lập và đầy đủ ngữ cảnh.
4. **Bộ Tools Nghiệp vụ Ngân hàng**:
   - `get_exchange_rate`: Tra tỷ giá ngoại tệ thực tế từ REST API.
   - `check_card_status_mock`: Tra cứu trạng thái khóa thẻ.
   - `calculate_savings_interest`: Tính toán tiền lãi tiết kiệm và tổng tiền thu về khi đáo hạn.
   - `search_atm_branch_mock`: Tra cứu chi nhánh và vị trí cây ATM 24/7 theo khu vực.
5. **Bảo mật & An toàn Dữ liệu (PII Redactor)**:
   - Tự động phát hiện và mờ hóa số CCCD (12 chữ số), Số thẻ (16 chữ số) và Mã OTP khẩn cấp trước khi đưa vào Agent/LLM.
6. **RAG Citations & Knowledge Search**:
   - Tra cứu tri thức tin tức/quy trình ngân hàng từ Chroma Vector DB với E5 Embeddings và đính kèm nguồn trích dẫn (`📌 Nguồn tham khảo`).
7. **FastAPI SSE Streaming & Modern Web UI**:
   - Streaming câu trả lời từng token thời gian thực (SSE).
   - Sidebar Drawer quản lý danh sách cuộc trò chuyện cũ.
   - **Voice Chat**: Nhận diện giọng nói tiếng Việt (Speech-to-Text) và phát âm thanh câu trả lời (Text-to-Speech).
   - Nút Sao chép (Copy) và Đánh giá (Like/Dislike).

---

## 🛠️ Nguồn gốc từng thành phần

| Thành phần | Nguồn / Công nghệ |
|---|---|
| Model Phân loại | `phobert-banking-aspect`, `phobert-banking-sentiment` (Fine-tune trên Kaggle) |
| Vector Store (RAG) | Chroma DB (`chroma_banking_news`) + HuggingFace E5 Embeddings |
| Checkpointer & Memory | LangGraph `SqliteSaver` (`banking_chat.db`) |
| Generative LLM | Gemini API (`gemini-2.0-flash` / `gemini-1.5-flash`) |
| Web UI & Voice | Vanilla HTML/CSS/JS + Web Speech API (STT/TTS) |

---

## 🚀 Hướng dẫn Chạy Local

### 1. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### 2. Tải & Giải nén Chroma DB

Tải `chroma_banking_news.zip` từ Kaggle output (Save Version của notebook fine-tune), giải nén vào thư mục gốc project:

```bash
unzip chroma_banking_news.zip -d chroma_banking_news
```

### 3. Cấu hình `.env`

Copy `.env.example` ➡️ `.env` và điền `GEMINI_API_KEY`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Khởi chạy Server

```bash
uvicorn api:app --reload
```

Mở trình duyệt truy cập: `http://localhost:8000`

---

## 🐳 Khởi chạy bằng Docker

```bash
docker compose up --build
```

---

## 🧪 Khởi chạy Unit Tests

Chạy toàn bộ 16 test cases kiểm thử logic routing, API schema, tools, PII redactor, Query rewriter và SqliteSaver:

```bash
pytest tests/ -v
```

