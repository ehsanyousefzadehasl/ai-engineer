
import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from agent import Agent
from llm import OllamaLLM
from tool_executor import ToolExecutor


async def main():
    server_path = Path(__file__).with_name("mcp_server.py")

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with Client(server) as mcp_client:
        llm = OllamaLLM(model="qwen3:4b")
        executor = ToolExecutor(mcp_client)

        agent = Agent(
            llm=llm,
            tool_executor=executor,
            max_steps=5,
        )

        request = input("Ask the agent: ")
        answer = await agent.run(request)

        print("\nAgent:", answer)


if __name__ == "__main__":
    asyncio.run(main())
