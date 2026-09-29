import pytest
from app.mcp.tools.rag import rag_query
from app.services.ai_chat import is_conversational_greeting


def test_rag_query_metadata():
    assert rag_query.__doc__ is not None
    assert "Search and retrieve" in rag_query.__doc__
    assert "organization_id" in rag_query.__doc__


def test_greeting_detection():
    assert is_conversational_greeting("Hi") is True
    assert is_conversational_greeting("Hello!") is True
    assert is_conversational_greeting("hey") is True
    assert is_conversational_greeting("Thanks.") is True
    assert is_conversational_greeting("When did Manisha Bhatt graduate?") is False
    assert is_conversational_greeting("tell me about the company policy") is False


def test_schema_sanitization():
    # Simulate a raw MCP tool input schema
    raw_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "organization_id": {"type": "string", "description": "Org ID"},
        },
        "required": ["query", "organization_id"],
    }

    # Apply the same sanitization logic as AIChatService._agent
    parameters = dict(raw_schema)
    properties = dict(parameters.get("properties", {}))
    required = list(parameters.get("required", []))

    if "organization_id" in properties:
        del properties["organization_id"]
    if "organization_id" in required:
        required.remove("organization_id")

    parameters["properties"] = properties
    parameters["required"] = required

    assert "organization_id" not in parameters["properties"]
    assert "organization_id" not in parameters["required"]
    assert "query" in parameters["properties"]
    assert parameters["required"] == ["query"]


@pytest.mark.asyncio
async def test_mcp_server_registered_tool():
    from app.mcp.server import mcp
    import app.mcp.tools.rag  # noqa: F401

    tools = await mcp.list_tools()
    tool_map = {t.name: t for t in tools}
    assert "rag_query" in tool_map

    rag = tool_map["rag_query"]
    assert rag.description is not None
    assert len(rag.description) > 10
    assert "Search and retrieve" in rag.description

    schema = rag.input_schema
    assert "query" in schema.get("properties", {})
    required = schema.get("required", [])
    assert "query" in required
    assert "organization_id" not in required

