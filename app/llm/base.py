"""Abstract Base LLM Interface and Data Types."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class LLMMessage(BaseModel):
    """Normalized chat message representation across LLM providers."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ToolParameterSchema(BaseModel):
    """Schema for tool function parameters."""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    """Provider-agnostic tool definition for function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolCallRequest(BaseModel):
    """Structured tool call invocation produced by the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


class TokenUsage(BaseModel):
    """Token usage telemetry."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    content: Optional[str] = None
    tool_calls: List[ToolCallRequest] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: Optional[str] = None
    interaction_id: Optional[str] = None
    raw_response: Optional[Any] = Field(default=None, exclude=True)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseLLMClient(ABC):
    """Abstract interface for LLM provider clients."""

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        system_instruction: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        previous_interaction_id: Optional[str] = None,
    ) -> LLMResponse:
        """Generate a response or function call given a conversation history."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """Generate guaranteed structured output parsed into a Pydantic model."""
        pass
