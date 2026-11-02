import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def select_tool(request: tool) -> str | None:
    """simple rule-based tool selection."""
    if "gpu" in request.lower():
        return "gpu_status"
    return None


async def main():
    request = input("Ask the agent: ")
    tool_name = select_tool(request)

    if tool_name is None:
        print("No suitable tool selected.")
        return
    
    server = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()

            print("Available tools: ", [t.name for t in tools.tools])

            result = await session.call_tool("gpu_status", {})
            print("GPU status:", result.structured_content or result.content)


if __name__ == "__main__":
    asyncio.run(main())