import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
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