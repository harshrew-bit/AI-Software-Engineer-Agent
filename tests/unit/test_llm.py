"""Unit tests for BaseLLMClient interface, MockLLMClient, and factory."""

import pytest
from pydantic import BaseModel
from app.llm.base import LLMMessage, LLMResponse, ToolCallRequest
from app.llm.factory import get_llm_client
from app.llm.mock import MockLLMClient


class SimpleResponseModel(BaseModel):
    summary: str
    confidence_score: float


@pytest.mark.asyncio
async def test_mock_llm_generate():
    """Verify mock client text generation."""
    mock = MockLLMClient(default_response="Plan generated successfully.")
    messages = [LLMMessage(role="user", content="Create a plan for adding auth.")]
    response = await mock.generate(messages)

    assert response.content == "Plan generated successfully."
    assert len(mock.call_history) == 1
    assert mock.call_history[0]["messages"][0].content == "Create a plan for adding auth."


@pytest.mark.asyncio
async def test_mock_llm_structured_output():
    """Verify structured output parsing with Mock client."""
    mock = MockLLMClient()
    mock.set_structured_response(
        "SimpleResponseModel",
        {"summary": "Refactor completed", "confidence_score": 0.98},
    )

    result = await mock.generate_structured(
        prompt="Analyze the code",
        response_schema=SimpleResponseModel,
    )
    assert result.summary == "Refactor completed"
    assert result.confidence_score == 0.98


@pytest.mark.asyncio
async def test_mock_llm_canned_tool_call():
    """Verify tool call responses."""
    canned = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_1",
                name="read_file",
                arguments={"file_path": "main.py"},
            )
        ],
    )
    mock = MockLLMClient()
    mock.add_canned_response(canned)

    resp = await mock.generate([LLMMessage(role="user", content="Read main.py")])
    assert resp.has_tool_calls is True
    assert resp.tool_calls[0].name == "read_file"
    assert resp.tool_calls[0].arguments == {"file_path": "main.py"}


def test_llm_factory_selection():
    """Test factory resolution of mock and gemini providers."""
    mock_client = get_llm_client(provider="mock")
    assert isinstance(mock_client, MockLLMClient)

    gemini_client = get_llm_client(provider="gemini", api_key="dummy_key")
    assert gemini_client.api_key == "dummy_key"
