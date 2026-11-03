
import asyncio
import json
import sys
import time

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

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a GPU infrastructure assistant. "
                        "For GPU memory feasibility questions, first call "
                        "gpu_status to obtain available_memory_gb. "
                        "Then call estimate_training_fit using that value "
                        "and the user's required memory. "
                        "Do not invent GPU measurements. "
                        "The GPU data is mocked for demonstration."
                    ),
                },
                {"role": "user", "content": request},
            ]



            MAX_STEPS = 5

            for step in range(MAX_STEPS):
                print(f"\nAgent step {step + 1}")

                response = await llm.chat(
                    model=MODEL,
                    messages=messages,
                    tools=tools,
                )

                messages.append(response.message)
                calls = response.message.tool_calls or []


                print("Selected tools:", [c.function.name for c in calls])

                
                # No tool calls means the agent is finished
                if not calls:
                    print("\nAgent:", response.message.content)
                    break


                async def execute_tool(call):
                    name = call.function.name
                    args = call.function.arguments

                    if name not in allowed:
                        output = f"Tool '{name}' is not allowed."
                    else:
                        try:
                            result = await asyncio.wait_for(
                                mcp.call_tool(name, args),
                                timeout=15,
                            )
                            output = json.dumps(
                                result.model_dump(mode="json")
                            )
                        except Exception as exc:
                            output = f"Tool failed: {exc}"

                    print(f"Executed: {name}")
                    return {
                        "role": "tool",
                        "tool_name": name,
                        "content": output,
                    }

                start = time.perf_counter()

                results = await asyncio.gather(
                    *(execute_tool(call) for call in calls)
                )

                messages.extend(results)

                elapsed = time.perf_counter() - start
                print(f"Tool execution time: {elapsed:.2f}s")


            else:
                print("\nStopped: maximum agent steps reached.")


if __name__ == "__main__":
    asyncio.run(main())
