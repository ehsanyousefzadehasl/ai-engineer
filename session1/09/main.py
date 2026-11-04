# added for the sake of bootstrapping
import logging
from config import settings
from logging_config import setup_logging
# ------ checkout

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from agent import Agent
from llm import OllamaLLM
from tool_executor import ToolExecutor

# this is for request tracing
import time
import uuid

async def main():
    # added for bootstarping instead of having them hardcoded in the code
    setup_logging(settings.log_level)
    logger = logging.getLogger("agent")

    logger.info("Starting agent")

    server_path = Path(__file__).with_name("mcp_server.py")

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with Client(server) as mcp_client:
        # llm = OllamaLLM(model="qwen3:4b")
        # commented

        llm = OllamaLLM(model=settings.model)

        executor = ToolExecutor(mcp_client)


        # agent = Agent(
        #     llm=llm,
        #     tool_executor=executor,
        #     max_steps=5,
        # )
        agent = Agent(
            llm=llm,
            tool_executor=executor,
            max_steps=settings.max_steps,
        )

        request = input("Ask the agent: ")

        request_id = uuid.uuid4().hex
        start = time.perf_counter()

        logger.info(
            "Agent request started",
            extra={"request_id": request_id},
        )

        try:
            answer = await agent.run(request)
            print("\nAgent:", answer)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000

            logger.info(
                "Agent request finished",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(elapsed_ms, 2),
                },
            )


        print("\nAgent:", answer)


if __name__ == "__main__":
    asyncio.run(main())
