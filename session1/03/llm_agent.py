import asyncio
import json
import sys

from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    llm = AsyncOpenAI()

    server = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
    )


    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as mcp:
            await mcp.initialize()

            # discovering all available tools
            discovered = (await mcp.list_tools()).tools
            allowed = {tool.name for tool in discovered}

            # here now we have all the info about the tools list
            tools = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                }
                for tool in discovered
            ]


            request = input("Ask the agent: ")
            # here the input which comes from user instead of being handled by the simple rule we had earlier

            # will be given to the llm, and the llm will select one based on the input :)
            # =================================
            # First LLM call — Decision making
            # =================================

            # The LLM receives the user's request and available tool descriptions.
            # It decides whether to:
            # - Answer directly without a tool.
            # - Request a tool call, such as gpu_status, with appropriate arguments.
            # Important: The LLM does not execute the tool. Our Python application does that through MCP.

            response = await llm.responses.create(
                model="gpt-4.1-mini",
                input=request,
                tools=tools,
            )


            # One tool-calling round for now
            results = []

            for item in response.output:
                # if it is not a function call, then we jump over it
                if item.type != "function_call":
                    continue

                # if the tool is not allowed, we should make it clear as unauthorized tool
                if item.name not in allowed:
                    raise ValueError("Unauthorized tool")


                arguments = json.loads(item.arguments)
                print("LLM selected:", item.name, arguments)

                # the tool is going to be called by the client from the server and its result will be used, read as follows
                result = await mcp.call_tool(
                    item.name, arguments
                )

                results.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(
                        result.model_dump(mode="json")
                    ),
                })

            # Second LLM call — Interpreting results
            # After our application executes the selected tool, the LLM receives the result and generates a natural-language answer.
            
            if results:
                response = await llm.responses.create(
                    model="gpt-4.1-mini",
                    previous_response_id=response.id,
                    input=results,
                    tools=tools,
                    tool_choice="none",
                )

            print("Agent:", response.output_text)


if __name__ == "__main__":
    asyncio.run(main())