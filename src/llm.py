"""LLM factory — tách riêng để dễ đổi provider (Gemini free tier mặc định,
đổi sang OpenAI/Claude chỉ cần sửa hàm này, phần agent không cần đổi gì).

Sử dụng google-genai SDK trực tiếp (thay vì langchain-google-genai) để streaming
nội dung mượt mà và hỗ trợ tốt nhất các mô hình Gemini 2.0 / 1.5.
"""

from dataclasses import dataclass
from functools import lru_cache

from google import genai
from google.genai import types

from .config import settings


@dataclass
class LLMResponse:
    """Wrapper tối giản tương thích với interface LangChain (có thuộc tính .content)."""
    content: str


class GeminiLLM:
    """Thin wrapper quanh google-genai SDK, giữ đúng interface .invoke() / .stream()
    mà agent.py đang gọi."""

    def __init__(self, model: str, api_key: str, temperature: float = 0.3):
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.config = types.GenerateContentConfig(temperature=temperature)

    def _messages_to_contents(self, messages) -> tuple[str | None, str]:
        """Chuyển list[SystemMessage, HumanMessage] của LangChain sang format google-genai."""
        system_instruction = None
        user_text = ""
        for msg in messages:
            role = getattr(msg, "type", "human")
            if role == "system":
                system_instruction = msg.content
            else:
                user_text = msg.content
        return system_instruction, user_text

    def invoke(self, messages) -> LLMResponse:
        system_instruction, user_text = self._messages_to_contents(messages)
        config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            system_instruction=system_instruction,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_text,
            config=config,
        )
        return LLMResponse(content=response.text or "")

    def stream(self, messages):
        system_instruction, user_text = self._messages_to_contents(messages)
        config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            system_instruction=system_instruction,
        )
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=user_text,
            config=config,
        ):
            if chunk.text:
                yield LLMResponse(content=chunk.text)


@lru_cache(maxsize=1)
def get_llm() -> GeminiLLM:
    return GeminiLLM(
        model=settings.gemini_model,
        api_key=settings.gemini_api_key,
        temperature=0.3,
    )
