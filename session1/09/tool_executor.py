
import asyncio
import json

from jsonschema import validate, ValidationError


class ToolExecutor:
    SAFE_TOOLS = {
        "gpu_status",
        "gpu_utilization",
        "gpu_temperature",
        "estimate_training_fit",
    }

    def __init__(self, mcp_client):
        self.client = mcp_client
        self.schemas = {}

    async def discover(self):
        discovered = (await self.client.list_tools()).tools

        self.schemas = {
            tool.name: tool.input_schema
            for tool in discovered
            if tool.name in self.SAFE_TOOLS
        }

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
            for tool in discovered
            if tool.name in self.schemas
        ]

    async def execute(self, call):
        name = call.function.name
        args = call.function.arguments

        try:
            if name not in self.schemas:
                raise ValueError("Tool not authorized")

            if isinstance(args, str):
                args = json.loads(args)

            validate(instance=args, schema=self.schemas[name])

            for attempt in range(2):
                try:
                    result = await asyncio.wait_for(
                        self.client.call_tool(name, args),
                        timeout=5,
                    )

                    if result.is_error:
                        raise ValueError(
                            f"MCP tool error: {result.content}"
                        )

                    output = json.dumps(
                        result.model_dump(mode="json")
                    )
                    break

                except TimeoutError:
                    if attempt == 1:
                        raise
                    await asyncio.sleep(0.5)

        except (ValueError, ValidationError, TimeoutError) as exc:
            output = f"Tool execution failed: {exc}"
        except Exception as exc:
            output = (
                f"Tool execution failed: "
                f"{type(exc).__name__}"
            )

        print(f"Tool executed: {name}")

        return {
            "role": "tool",
            "tool_name": name,
            "content": output,
        }
