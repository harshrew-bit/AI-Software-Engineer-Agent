"""OpenAI LLM Provider Implementation."""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.config import get_settings
from app.llm.base import (
    BaseLLMClient,
    LLMMessage,
    LLMResponse,
    TokenUsage,
    ToolCallRequest,
    ToolDefinition,
)

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OpenAILLMClient(BaseLLMClient):
    """Production OpenAI LLM Client supporting Chat Completions, Function Calling, and Structured Outputs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model_name = model_name or settings.openai_model or "gpt-4o-mini"
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.max_retries = settings.openai_max_retries
        self.retry_delay_seconds = settings.openai_retry_delay_seconds
        self._client = None
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    def _get_client(self):
        """Lazy client instantiation using official AsyncOpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                raise
        return self._client

    def _format_tools_for_openai(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert ToolDefinitions into OpenAI function calling format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return openai_tools

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Return True when the error represents rate limiting or quota exhaustion (429)."""
        status_code = (
            getattr(error, "status_code", None)
            or getattr(error, "status", None)
            or getattr(error, "code", None)
        )
        if str(status_code) == "429":
            return True

        error_text = str(error).lower()
        return (
            "429" in error_text
            or "rate limit" in error_text
            or "too many requests" in error_text
            or "quota" in error_text
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        previous_interaction_id: Optional[str] = None,
    ) -> LLMResponse:
        """Generate text or function calls using OpenAI Chat Completions API with multi-turn history tracking."""
        client = self._get_client()

        # Build message history for the OpenAI request
        if previous_interaction_id and previous_interaction_id in self._history:
            chat_messages = list(self._history[previous_interaction_id])
            for msg in messages:
                if msg.role == "tool":
                    chat_messages.append({
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id or f"call_{msg.name}",
                    })
                elif msg.role in ("user", "assistant", "system"):
                    chat_messages.append({
                        "role": msg.role,
                        "content": msg.content,
                    })
        else:
            chat_messages = []
            if system_instruction:
                chat_messages.append({"role": "system", "content": system_instruction})
            for msg in messages:
                if msg.role == "system":
                    chat_messages.append({"role": "system", "content": msg.content})
                elif msg.role == "user":
                    chat_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    chat_messages.append({"role": "assistant", "content": msg.content})
                elif msg.role == "tool":
                    chat_messages.append({
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id or f"call_{msg.name}",
                    })

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": list(chat_messages),
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        if tools:
            kwargs["tools"] = self._format_tools_for_openai(tools)

        # Call OpenAI with bounded retry logic
        response = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.chat.completions.create(**kwargs)
                break
            except Exception as e:
                if not self._is_rate_limit_error(e):
                    logger.error(f"OpenAI API invocation error: {e}")
                    raise
                if attempt >= self.max_retries:
                    logger.error(f"OpenAI rate limit persisted after {self.max_retries} retries: {e}")
                    raise
                logger.warning(
                    f"OpenAI rate limit (429). Retry {attempt + 1}/{self.max_retries} in {self.retry_delay_seconds}s"
                )
                await asyncio.sleep(self.retry_delay_seconds)

        choice = response.choices[0]
        msg = choice.message
        content = msg.content

        tool_calls: List[ToolCallRequest] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = tc.id
                tc_name = tc.function.name
                try:
                    tc_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                except Exception:
                    tc_args = {"raw": tc.function.arguments}
                tool_calls.append(ToolCallRequest(id=tc_id, name=tc_name, arguments=tc_args))

        # Record assistant message in history
        assistant_history_entry: Dict[str, Any] = {
            "role": "assistant",
            "content": content or "",
        }
        if msg.tool_calls:
            assistant_history_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments if isinstance(tc.function.arguments, str) else json.dumps(tc.function.arguments),
                    },
                }
                for tc in msg.tool_calls
            ]
        chat_messages.append(assistant_history_entry)

        new_interaction_id = f"openai_{uuid.uuid4().hex[:12]}"
        self._history[new_interaction_id] = chat_messages

        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=choice.finish_reason or ("tool_calls" if tool_calls else "stop"),
            interaction_id=new_interaction_id,
            raw_response=response,
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """Generate structured Pydantic output using OpenAI Structured Outputs with JSON schema fallback."""
        client = self._get_client()

        messages: List[Dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        # Try beta.chat.completions.parse for guaranteed structured output
        for attempt in range(self.max_retries + 1):
            try:
                parse_response = await client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=messages,
                    response_format=response_schema,
                    temperature=temperature if temperature is not None else self.temperature,
                )
                parsed = parse_response.choices[0].message.parsed
                if parsed is not None:
                    return parsed
            except Exception as e:
                if self._is_rate_limit_error(e) and attempt < self.max_retries:
                    logger.warning(f"OpenAI rate limit during structured parse. Retrying in {self.retry_delay_seconds}s")
                    await asyncio.sleep(self.retry_delay_seconds)
                    continue
                logger.debug(f"Native structured parse fell back to JSON completion: {e}")
                break

        # Fallback: standard JSON mode with schema instruction
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        fallback_prompt = (
            f"{prompt}\n\n"
            f"CRITICAL: Respond ONLY with a valid JSON object strictly conforming to this schema:\n"
            f"{schema_json}"
        )
        fallback_messages: List[Dict[str, str]] = []
        if system_instruction:
            fallback_messages.append({"role": "system", "content": system_instruction})
        fallback_messages.append({"role": "user", "content": fallback_prompt})

        for attempt in range(self.max_retries + 1):
            try:
                raw_resp = await client.chat.completions.create(
                    model=self.model_name,
                    messages=fallback_messages,
                    response_format={"type": "json_object"},
                    temperature=temperature if temperature is not None else self.temperature,
                )
                content = raw_resp.choices[0].message.content or "{}"
                return response_schema.model_validate_json(content)
            except Exception as e:
                if self._is_rate_limit_error(e) and attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay_seconds)
                    continue
                logger.error(f"OpenAI structured fallback error: {e}")
                raise
