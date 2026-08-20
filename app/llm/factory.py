"""LLM Provider Factory."""

from typing import Optional
from app.config import get_settings
from app.llm.base import BaseLLMClient
from app.llm.gemini import GeminiLLMClient
from app.llm.mock import MockLLMClient
from app.llm.openai import OpenAILLMClient


def get_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> BaseLLMClient:
    """Factory creating LLM client according to settings or explicit arguments."""
    settings = get_settings()
    selected_provider = (provider or settings.default_llm_provider).lower()

    if selected_provider == "gemini":
        return GeminiLLMClient(
            api_key=api_key or settings.gemini_api_key,
            model_name=model_name or settings.gemini_model,
        )
    elif selected_provider == "openai":
        return OpenAILLMClient(
            api_key=api_key or settings.openai_api_key,
            model_name=model_name or settings.openai_model,
        )
    elif selected_provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{selected_provider}'. Supported: 'gemini', 'openai', 'mock'."
        )
