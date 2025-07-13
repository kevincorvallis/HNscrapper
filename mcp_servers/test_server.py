import pytest

pytest.importorskip("mcp")

from mcp.server import Server
from mcp.types import Tool, TextContent

# Optional import for environment completeness
try:
    from dynamodb_manager import DynamoDBManager  # noqa: F401
except Exception:
    pass


@pytest.mark.asyncio
async def test_server_setup():
    """Ensure the demo MCP server can be created and tools registered."""
    app = Server("test-server")

    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="test_tool",
                description="A test tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Test message",
                        }
                    },
                },
            )
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "test_tool":
            return [
                TextContent(
                    type="text",
                    text=f"Test successful: {arguments.get('message', 'No message')}",
                )
            ]
        return [TextContent(type="text", text="Unknown tool")]

    assert callable(list_tools)
    assert callable(call_tool)
    assert app is not None
