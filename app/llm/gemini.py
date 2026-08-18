"""Google Gemini LLM Implementation."""

import json
import logging
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


class GeminiLLMClient(BaseLLMClient):
    """Production Gemini LLM Client using Google GenAI SDK with structured output & function calling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        # Default to gemini-3.6-flash or configured model
        self.model_name = model_name or settings.gemini_model or "gemini-3.6-flash"
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self._client = None

    def _get_client(self):
        """Lazy client instantiation."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI client: {e}")
                raise
        return self._client

    def _format_tools_for_gemini(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert ToolDefinitions into Gemini Interactions API function tool format."""
        gemini_tools = []
        for tool in tools:
            gemini_tools.append({
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            })
        return gemini_tools

    async def generate(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        previous_interaction_id: Optional[str] = None,
    ) -> LLMResponse:
        """Generate response or function calls from Gemini with support for structured function results."""
        client = self._get_client()

        # Check if this is a tool-result follow-up turn using previous_interaction_id
        tool_messages = [msg for msg in messages if msg.role == "tool"]

        if previous_interaction_id and tool_messages:
            # Build structured function_result list for Gemini Interactions API
            structured_input: List[Dict[str, Any]] = []
            for msg in tool_messages:
                structured_input.append({
                    "type": "function_result",
                    "name": msg.name,
                    "call_id": msg.tool_call_id,
                    "result": [
                        {
                            "type": "text",
                            "text": msg.content,
                        }
                    ],
                })

            kwargs: Dict[str, Any] = {
                "model": self.model_name,
                "input": structured_input,
                "previous_interaction_id": previous_interaction_id,
            }
        else:
            # Initial interaction or standard text conversation: construct text prompt
            prompt_parts = []
            for msg in messages:
                if msg.role == "system" and not system_instruction:
                    system_instruction = msg.content
                elif msg.role in ("user", "assistant"):
                    prompt_parts.append(msg.content if len(messages) == 1 and msg.role == "user" else f"[{msg.role.upper()}]: {msg.content}")

            combined_input = "\n\n".join(prompt_parts) if prompt_parts else ""

            kwargs: Dict[str, Any] = {
                "model": self.model_name,
                "input": combined_input,
            }

            if system_instruction:
                kwargs["system_instruction"] = system_instruction

            if previous_interaction_id:
                kwargs["previous_interaction_id"] = previous_interaction_id

        # Tools are interaction-scoped and must be re-specified on each turn
        if tools:
            kwargs["tools"] = self._format_tools_for_gemini(tools)

        # Call Gemini Interactions API
        try:
            interaction = client.interactions.create(**kwargs)

            # Extract output text and tool calls if any
            content = getattr(interaction, "output_text", None)
            interaction_id = getattr(interaction, "id", None)
            tool_calls: List[ToolCallRequest] = []

            # Check steps for function calls if present
            steps = getattr(interaction, "steps", [])
            for step in steps:
                step_type = getattr(step, "type", None)
                if step_type in ("function_call", "tool_call"):
                    fc_name = getattr(step, "name", "")
                    fc_args = getattr(step, "arguments", {})
                    fc_id = getattr(step, "id", f"call_{fc_name}")
                    if isinstance(fc_args, str):
                        try:
                            fc_args = json.loads(fc_args)
                        except Exception:
                            fc_args = {"raw": fc_args}
                    tool_calls.append(
                        ToolCallRequest(id=fc_id, name=fc_name, arguments=fc_args)
                    )

            # Usage tracking
            usage_obj = getattr(interaction, "usage", None)
            usage = TokenUsage(
                prompt_tokens=getattr(usage_obj, "prompt_tokens", 0) if usage_obj else 0,
                completion_tokens=getattr(usage_obj, "completion_tokens", 0) if usage_obj else 0,
                total_tokens=getattr(usage_obj, "total_tokens", 0) if usage_obj else 0,
            )

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                usage=usage,
                finish_reason="stop" if not tool_calls else "tool_calls",
                interaction_id=interaction_id,
                raw_response=interaction,
            )

        except Exception as e:
            logger.error(f"Gemini API invocation error: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """Generate structured Pydantic output using schema constraint."""
        client = self._get_client()

        json_schema_prompt = (
            f"{prompt}\n\n"
            f"CRITICAL: Respond ONLY with valid JSON matching the following JSON Schema:\n"
            f"{json.dumps(response_schema.model_json_schema(), indent=2)}"
        )

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "input": json_schema_prompt,
        }
        if system_instruction:
            kwargs["system_instruction"] = system_instruction

        interaction = client.interactions.create(**kwargs)
        raw_text = getattr(interaction, "output_text", "")

        # Clean JSON markdown fences if present
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()

        return response_schema.model_validate_json(cleaned_text)
