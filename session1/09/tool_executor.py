
import asyncio
import json

from jsonschema import validate, ValidationError


# the following ones are added for 
# the sake of error classification and
# logging

import logging
import random

from config import settings
from errors import (
    ToolAuthorizationError,
    ToolValidationError,
    ToolExecutionError,
    ToolTimeoutError,
)
from mcp import MCPError

logger = logging.getLogger("agent.tools")

# end of that part for error classification and logging

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
            # 1. Authorization
            if name not in self.schemas:
                raise ToolAuthorizationError(
                    "Tool not authorized"
                )

            # 2. Argument parsing and validation
            try:
                if isinstance(args, str):
                    args = json.loads(args)

                validate(args, self.schemas[name])

            except (ValueError, TypeError, ValidationError) as exc:
                raise ToolValidationError(
                    "Invalid tool arguments"
                ) from exc

            # 3. Controlled retries
            # Only these mock read-only tools are retryable.
            retryable_tools = {
                "gpu_status",
                "gpu_utilization",
                "gpu_temperature",
                "estimate_training_fit",
            }

            max_attempts = 3 if name in retryable_tools else 1

            for attempt in range(max_attempts):
                try:
                    result = await asyncio.wait_for(
                        self.client.call_tool(name, args),
                        timeout=settings.tool_timeout,
                    )

                    if result.is_error:
                        raise ToolExecutionError(
                            "MCP tool reported an error"
                        )

                    output = json.dumps(
                        result.model_dump(mode="json")
                    )
                    break

                except TimeoutError as exc:
                    if attempt == max_attempts - 1:
                        raise ToolTimeoutError(
                            "Tool timed out after retries"
                        ) from exc

                    delay = min(
                        0.5 * (2 ** attempt), 4.0
                    ) + random.uniform(0, 0.2)

                    logger.warning(
                        "Retrying timed-out tool",
                        extra={"tool": name},
                    )
                    await asyncio.sleep(delay)

        except (
            ToolAuthorizationError,
            ToolValidationError,
            ToolExecutionError,
            ToolTimeoutError,
        ) as exc:
            logger.warning(
                "%s",
                type(exc).__name__,
                extra={"tool": name},
            )
            output = f"{type(exc).__name__}: {exc}"

        except MCPError:
            logger.exception(
                "MCP protocol failure",
                extra={"tool": name},
            )
            output = "ToolExecutionError: MCP request failed"

        except Exception:
            logger.exception(
                "Unexpected tool failure",
                extra={"tool": name},
            )
            output = "ToolExecutionError: Internal failure"

        return {
            "role": "tool",
            "tool_name": name,
            "content": output,
        }
