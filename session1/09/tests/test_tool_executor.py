
import asyncio
from types import SimpleNamespace as NS

from tool_executor import ToolExecutor


class FakeMCP:
    def __init__(self):
        self.calls = []

    async def list_tools(self):
        return NS(tools=[
            NS(
                name="estimate_training_fit",
                description="Check memory feasibility",
                input_schema={
                    "type": "object",
                    "properties": {
                        "required_memory_gb": {
                            "type": "number",
                            "minimum": 0,
                        },
                        "available_memory_gb": {
                            "type": "number",
                            "minimum": 0,
                        },
                    },
                    "required": [
                        "required_memory_gb",
                        "available_memory_gb",
                    ],
                    "additionalProperties": False,
                },
            ),
        ])

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        return NS(
            is_error=False,
            model_dump=lambda **kwargs: {"ok": True},
        )


def call(name, args):
    return NS(function=NS(name=name, arguments=args))


def test_unauthorized_tool():
    async def scenario():
        client = FakeMCP()
        executor = ToolExecutor(client)
        await executor.discover()

        result = await executor.execute(
            call("delete_files", {})
        )

        assert "not authorized" in result["content"]
        assert client.calls == []

    asyncio.run(scenario())


def test_invalid_arguments():
    async def scenario():
        client = FakeMCP()
        executor = ToolExecutor(client)
        await executor.discover()

        result = await executor.execute(
            call("estimate_training_fit", {
                "available_memory_gb": 40,
                "required_memory_gb": -5,
            })
        )

        assert "failed" in result["content"].lower()
        assert client.calls == []

    asyncio.run(scenario())
