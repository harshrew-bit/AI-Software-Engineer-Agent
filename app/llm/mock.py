"""Deterministic Mock LLM Client for Testing and Dry-runs."""

import json
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.llm.base import (
    BaseLLMClient,
    LLMMessage,
    LLMResponse,
    TokenUsage,
    ToolCallRequest,
    ToolDefinition,
)

T = TypeVar("T", bound=BaseModel)


class MockLLMClient(BaseLLMClient):
    """Configurable mock LLM client returning scripted responses or simulated tool calls."""

    def __init__(
        self,
        default_response: str = "Mocked LLM Response",
        canned_responses: Optional[List[LLMResponse]] = None,
        structured_responses: Optional[Dict[str, Any]] = None,
        custom_handler: Optional[Callable[[List[LLMMessage]], LLMResponse]] = None,
    ):
        self.default_response = default_response
        self.canned_responses: List[LLMResponse] = canned_responses or []
        self.structured_responses: Dict[str, Any] = structured_responses or {}
        self.custom_handler = custom_handler
        self.call_history: List[Dict[str, Any]] = []

    def add_canned_response(self, response: LLMResponse) -> None:
        """Enqueue a canned response to be returned in sequence."""
        self.canned_responses.append(response)

    def set_structured_response(self, schema_name: str, data: Any) -> None:
        """Register a response object for a given Pydantic schema class name."""
        self.structured_responses[schema_name] = data

    async def generate(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        previous_interaction_id: Optional[str] = None,
    ) -> LLMResponse:
        """Return scripted response or invoke custom handler."""
        self.call_history.append({
            "type": "generate",
            "messages": messages,
            "system_instruction": system_instruction,
            "tools": tools,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "previous_interaction_id": previous_interaction_id,
        })

        if self.custom_handler:
            return self.custom_handler(messages)

        if self.canned_responses:
            return self.canned_responses.pop(0)

        return LLMResponse(
            content=self.default_response,
            tool_calls=[],
            usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
            finish_reason="stop",
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """Return structured Pydantic object."""
        self.call_history.append({
            "type": "generate_structured",
            "prompt": prompt,
            "schema": response_schema.__name__,
            "system_instruction": system_instruction,
        })

        schema_name = response_schema.__name__
        if schema_name in self.structured_responses:
            data = self.structured_responses[schema_name]
            if isinstance(data, response_schema):
                return data
            if isinstance(data, dict):
                return response_schema.model_validate(data)
            if isinstance(data, str):
                return response_schema.model_validate_json(data)

        # Fallback: instantiate schema with dummy fields if possible
        try:
            return response_schema.model_validate({})
        except Exception:
            raise ValueError(
                f"No mock response configured for schema {schema_name}. "
                f"Please use set_structured_response('{schema_name}', ...)"
            )
