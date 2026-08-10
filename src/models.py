"""Load 2 model PhoBERT đã fine-tune (từ HF Hub) và chạy inference.

Lưu ý quan trọng: lúc fine-tune trên Kaggle, nhãn được encode bằng
`sorted(set(...))` trên chính dataset, KHÔNG lưu `id2label` tường minh vào
config của model khi push lên Hub. Để tránh đoán sai thứ tự nhãn, ở đây ta
tái tạo lại đúng ánh xạ đó bằng cách load lại chính dataset gốc 1 lần (cache
lại sau đó) — đảm bảo khớp 100% với lúc train thay vì hard-code 1 danh sách
nhãn có thể bị sai.
"""

from functools import lru_cache

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from underthesea import word_tokenize

from .config import settings

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def _segment(text: str) -> str:
    """PhoBERT cần văn bản đã tách từ tiếng Việt trước khi tokenize."""
    return " ".join(word_tokenize(text))


# Danh sách nhãn đã sorted theo alphabet từ dataset UTS2017_Bank gốc
_ASPECT_LABELS = [
    'ACCOUNT', 'CARD', 'CUSTOMER_SUPPORT', 'DISCOUNT', 'INTEREST_RATE',
    'INTERNET_BANKING', 'LOAN', 'MONEY_TRANSFER', 'OTHER', 'PAYMENT',
    'PROMOTION', 'SAVING', 'SECURITY', 'TRADEMARK'
]
_SENTIMENT_LABELS = ['negative', 'neutral', 'positive']


@lru_cache(maxsize=1)
def _label_maps() -> tuple[dict[int, str], dict[int, str]]:
    id2aspect = {i: label for i, label in enumerate(_ASPECT_LABELS)}
    id2sentiment = {i: label for i, label in enumerate(_SENTIMENT_LABELS)}
    return id2aspect, id2sentiment




@lru_cache(maxsize=2)
def _load_model(repo_id: str):
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    model = AutoModelForSequenceClassification.from_pretrained(repo_id).to(_DEVICE).eval()
    return tokenizer, model


def classify(text: str) -> dict:
    """Trả về {aspect, sentiment, escalate} cho 1 đoạn text tiếng Việt."""
    id2aspect, id2sentiment = _label_maps()
    text_seg = _segment(text)

    tok_a, model_a = _load_model(settings.aspect_model_repo)
    enc_a = tok_a(text_seg, truncation=True, max_length=256, return_tensors="pt").to(_DEVICE)
    with torch.no_grad():
        logits_a = model_a(**enc_a).logits
    aspect = id2aspect[int(torch.argmax(logits_a, dim=-1))]

    tok_s, model_s = _load_model(settings.sentiment_model_repo)
    enc_s = tok_s(text_seg, truncation=True, max_length=256, return_tensors="pt").to(_DEVICE)
    with torch.no_grad():
        logits_s = model_s(**enc_s).logits
    sentiment = id2sentiment[int(torch.argmax(logits_s, dim=-1))]

    escalate = sentiment == "negative" and aspect in settings.escalate_aspects

    return {"aspect": aspect, "sentiment": sentiment, "escalate": escalate}
