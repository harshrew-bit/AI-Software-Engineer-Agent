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
    """Test factory resolution of mock, gemini, and openai providers."""
    mock_client = get_llm_client(provider="mock")
    assert isinstance(mock_client, MockLLMClient)

    gemini_client = get_llm_client(provider="gemini", api_key="dummy_gemini_key")
    assert gemini_client.api_key == "dummy_gemini_key"

    openai_client = get_llm_client(provider="openai", api_key="dummy_openai_key", model_name="gpt-4o-mini")
    from app.llm.openai import OpenAILLMClient
    assert isinstance(openai_client, OpenAILLMClient)
    assert openai_client.api_key == "dummy_openai_key"
    assert openai_client.model_name == "gpt-4o-mini"


# --- OpenAI LLM Client Unit Tests ---

@pytest.mark.asyncio
async def test_openai_generate_text(monkeypatch):
    """Verify OpenAILLMClient text generation with mocked OpenAI SDK."""
    from unittest.mock import AsyncMock, MagicMock
    from app.llm.openai import OpenAILLMClient

    client = OpenAILLMClient(api_key="test-key", model_name="gpt-4o-mini")

    mock_msg = MagicMock()
    mock_msg.content = "I am ready to help."
    mock_msg.tool_calls = None

    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_choice.finish_reason = "stop"

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.usage.prompt_tokens = 10
    mock_resp.usage.completion_tokens = 5
    mock_resp.usage.total_tokens = 15

    mock_openai = MagicMock()
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_resp)
    monkeypatch.setattr(client, "_get_client", lambda: mock_openai)

    messages = [LLMMessage(role="user", content="Hello")]
    response = await client.generate(messages, system_instruction="You are a helper.")

    assert response.content == "I am ready to help."
    assert response.has_tool_calls is False
    assert response.usage.total_tokens == 15
    assert response.interaction_id is not None

    # Verify call parameters
    mock_openai.chat.completions.create.assert_called_once()
    kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["messages"][0] == {"role": "system", "content": "You are a helper."}
    assert kwargs["messages"][1] == {"role": "user", "content": "Hello"}


@pytest.mark.asyncio
async def test_openai_generate_tool_calls(monkeypatch):
    """Verify OpenAILLMClient parses tool calls and arguments."""
    from unittest.mock import AsyncMock, MagicMock
    from app.llm.base import ToolDefinition
    from app.llm.openai import OpenAILLMClient

    client = OpenAILLMClient(api_key="test-key", model_name="gpt-4o-mini")

    mock_tc = MagicMock()
    mock_tc.id = "call_abc123"
    mock_tc.function.name = "create_file"
    mock_tc.function.arguments = '{"file_path": "main.py", "content": "print(1)"}'

    mock_msg = MagicMock()
    mock_msg.content = None
    mock_msg.tool_calls = [mock_tc]

    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_choice.finish_reason = "tool_calls"

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.usage = None

    mock_openai = MagicMock()
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_resp)
    monkeypatch.setattr(client, "_get_client", lambda: mock_openai)

    tool_def = ToolDefinition(
        name="create_file",
        description="Create a file",
        parameters={
            "type": "object",
            "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["file_path", "content"],
        },
    )

    messages = [LLMMessage(role="user", content="Create main.py")]
    response = await client.generate(messages, tools=[tool_def])

    assert response.has_tool_calls is True
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].id == "call_abc123"
    assert response.tool_calls[0].name == "create_file"
    assert response.tool_calls[0].arguments == {"file_path": "main.py", "content": "print(1)"}

    # Verify tool definition was correctly formatted for OpenAI
    kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert "tools" in kwargs
    assert kwargs["tools"][0]["function"]["name"] == "create_file"


@pytest.mark.asyncio
async def test_openai_multi_turn_tool_results(monkeypatch):
    """Verify OpenAILLMClient preserves conversation history across tool result follow-ups."""
    from unittest.mock import AsyncMock, MagicMock
    from app.llm.openai import OpenAILLMClient

    client = OpenAILLMClient(api_key="test-key", model_name="gpt-4o-mini")

    # Round 1: Model requests tool call
    tc1 = MagicMock()
    tc1.id = "call_step1"
    tc1.function.name = "list_files"
    tc1.function.arguments = "{}"

    msg1 = MagicMock()
    msg1.content = "Let me check the files."
    msg1.tool_calls = [tc1]

    choice1 = MagicMock()
    choice1.message = msg1
    choice1.finish_reason = "tool_calls"

    resp1 = MagicMock()
    resp1.choices = [choice1]
    resp1.usage = None

    # Round 2: Model finishes
    msg2 = MagicMock()
    msg2.content = "All files are listed."
    msg2.tool_calls = None

    choice2 = MagicMock()
    choice2.message = msg2
    choice2.finish_reason = "stop"

    resp2 = MagicMock()
    resp2.choices = [choice2]
    resp2.usage = None

    mock_openai = MagicMock()
    mock_openai.chat.completions.create = AsyncMock(side_effect=[resp1, resp2])
    monkeypatch.setattr(client, "_get_client", lambda: mock_openai)

    # 1. First turn: user prompt
    r1 = await client.generate(
        [LLMMessage(role="user", content="List directory")],
        system_instruction="Coder system",
    )
    assert r1.has_tool_calls is True
    inter_id = r1.interaction_id
    assert inter_id is not None

    # 2. Second turn: tool result follow-up with previous_interaction_id
    r2 = await client.generate(
        [LLMMessage(role="tool", content="main.py\nREADME.md", name="list_files", tool_call_id="call_step1")],
        previous_interaction_id=inter_id,
    )
    assert r2.content == "All files are listed."
    assert r2.has_tool_calls is False

    # Verify the second call received the full accumulated history
    call2_kwargs = mock_openai.chat.completions.create.call_args_list[1].kwargs
    history = call2_kwargs["messages"]
    assert len(history) == 4
    assert history[0]["role"] == "system"
    assert history[1]["role"] == "user"
    assert history[2]["role"] == "assistant"
    assert history[2]["tool_calls"][0]["id"] == "call_step1"
    assert history[3]["role"] == "tool"
    assert history[3]["tool_call_id"] == "call_step1"
    assert history[3]["content"] == "main.py\nREADME.md"


@pytest.mark.asyncio
async def test_openai_generate_structured(monkeypatch):
    """Verify OpenAILLMClient structured outputs with Pydantic model."""
    from unittest.mock import AsyncMock, MagicMock
    from app.llm.openai import OpenAILLMClient

    client = OpenAILLMClient(api_key="test-key", model_name="gpt-4o-mini")

    expected_output = SimpleResponseModel(summary="All tests passed", confidence_score=0.99)
    mock_parsed_msg = MagicMock()
    mock_parsed_msg.parsed = expected_output

    mock_parse_choice = MagicMock()
    mock_parse_choice.message = mock_parsed_msg

    mock_parse_resp = MagicMock()
    mock_parse_resp.choices = [mock_parse_choice]

    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(return_value=mock_parse_resp)
    monkeypatch.setattr(client, "_get_client", lambda: mock_openai)

    result = await client.generate_structured(
        prompt="Analyze results",
        response_schema=SimpleResponseModel,
        system_instruction="Reviewer system",
    )

    assert result.summary == "All tests passed"
    assert result.confidence_score == 0.99
    mock_openai.beta.chat.completions.parse.assert_called_once()


@pytest.mark.asyncio
async def test_openai_rate_limit_retry(monkeypatch):
    """Verify OpenAILLMClient retries bounded on 429 rate limit error."""
    from unittest.mock import AsyncMock, MagicMock
    from app.llm.openai import OpenAILLMClient

    client = OpenAILLMClient(api_key="test-key", model_name="gpt-4o-mini")
    client.retry_delay_seconds = 0.01

    class Mock429Error(Exception):
        status_code = 429

    mock_msg = MagicMock()
    mock_msg.content = "Recovered response"
    mock_msg.tool_calls = None

    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_choice.finish_reason = "stop"

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.usage = None

    mock_openai = MagicMock()
    # Fails once with 429, then succeeds
    mock_openai.chat.completions.create = AsyncMock(side_effect=[Mock429Error("Rate limit exceeded"), mock_resp])
    monkeypatch.setattr(client, "_get_client", lambda: mock_openai)

    response = await client.generate([LLMMessage(role="user", content="Ping")])
    assert response.content == "Recovered response"
    assert mock_openai.chat.completions.create.call_count == 2


def test_detect_test_command_pytest_glob(tmp_path):
    """Verify RunTestsTool detects pytest when test_*.py or requirements.txt has pytest."""
    from unittest.mock import MagicMock
    from app.tools.execution_tools import RunTestsTool
    from app.tools.base import ToolExecutionContext

    tool = RunTestsTool()

    # 1. Workspace with test_main.py
    ws1 = tmp_path / "ws1"
    ws1.mkdir()
    (ws1 / "test_main.py").write_text("def test_one(): pass\n")

    ctx1 = ToolExecutionContext(
        task_id="t1",
        workspace_path=ws1,
        git_manager=MagicMock(),
        sandbox=MagicMock(),
        settings=MagicMock(),
    )
    assert tool._detect_test_command(ctx1) == "pytest -v"

    # 2. Workspace with requirements.txt specifying pytest
    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    (ws2 / "requirements.txt").write_text("fastapi\npytest>=8.0.0\n")

    ctx2 = ToolExecutionContext(
        task_id="t2",
        workspace_path=ws2,
        git_manager=MagicMock(),
        sandbox=MagicMock(),
        settings=MagicMock(),
    )
    assert tool._detect_test_command(ctx2) == "pytest -v"
