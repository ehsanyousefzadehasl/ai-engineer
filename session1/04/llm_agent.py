
import asyncio
import json
import sys

from ollama import AsyncClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "qwen3:4b"


async def main():
    llm = AsyncClient()

    server = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as mcp:
            await mcp.initialize()

            discovered = (await mcp.list_tools()).tools
            allowed = {t.name for t in discovered}

            # Convert MCP tool schemas to Ollama schemas
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.input_schema,
                    },
                }
                for t in discovered
            ]

            request = input("Ask the agent: ")
            messages = [{"role": "user", "content": request}]

            # First LLM call: choose tools or answer
            response = await llm.chat(
                model=MODEL,
                messages=messages,
                tools=tools,
            )

            messages.append(response.message)

            # Execute all requested tool calls
            for call in response.message.tool_calls or []:
                name = call.function.name
                args = call.function.arguments

                if name not in allowed:
                    raise ValueError(f"Unauthorized tool: {name}")

                print(f"Calling MCP tool: {name}({args})")
                result = await mcp.call_tool(name, args)

                messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(
                        result.model_dump(mode="json")
                    ),
                })

            # Second LLM call: interpret tool results
            if response.message.tool_calls:
                response = await llm.chat(
                    model=MODEL,
                    messages=messages,
                    tools=[],
                )

            print("\nAgent:", response.message.content)


if __name__ == "__main__":
    asyncio.run(main())
