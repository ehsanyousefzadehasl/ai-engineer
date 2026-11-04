# With fake components, tests are:
# - Fast: No external API requests.
# - Deterministic: The LLM responses are predefined.
# - Isolated: Tests evaluate your agent's control logic.
# - Free: No inference API costs.

import asyncio

# SimpleNamespace lets you create objects with attributes without defining a class.
from types import SimpleNamespace as NS

from agent import Agent


# It creates a fake LLM response that supports:
# result.message.content
# result.message.tool_calls
def response(content="", calls=None):
    return NS(message=NS(
        content=content,
        tool_calls=calls or [],
    ))


# Similarly, tool_call() creates a fake tool-call object supporting:
# call.function.name
# call.function.arguments
def tool_call(name, args=None):
    return NS(function=NS(
        name=name,
        arguments=args or {},
    ))



# This simulates an LLM with predefined responses.
# - iter(responses) creates an iterator over the supplied responses.
# - next(self.responses) returns the next response each time chat() is called.
# - self.calls counts how many times the agent contacted the fake LLM.
class FakeLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    async def chat(self, messages, tools):
        self.calls += 1
        return next(self.responses)


class FakeExecutor:
    def __init__(self):
        # Records which tools ran
        self.executed = []
        # Counts tools currently executing
        self.active = 0
        # Records the highest number of simultaneously active tools
        self.max_active = 0

    # discover() returns an empty list 
    # because these tests don't need real tool discovery.
    async def discover(self):
        return []

    async def execute(self, call):
        self.active += 1
        self.max_active = max(
            self.max_active, self.active
        )

        # The artificial delay allows concurrent executions 
        # to overlap if your agent schedules them concurrently.
        await asyncio.sleep(0.05)

        name = call.function.name
        self.executed.append(name)
        self.active -= 1

        return {
            "role": "tool",
            "tool_name": name,
            "content": '{"ok": true}',
        }


# This verifies that the agent can execute a tool 
# and then obtain a final response.
def test_agent_tool_loop():
    async def scenario():
        llm = FakeLLM([
            response(calls=[tool_call("gpu_status")]),
            response(content="GPU available"),
        ])
        executor = FakeExecutor()
        agent = Agent(llm, executor)

        answer = await agent.run("Check GPU")

        # if the results are sth different, then 
        # it will fail :)
        assert answer == "GPU available"
        assert executor.executed == ["gpu_status"]
        assert llm.calls == 2

    asyncio.run(scenario())


def test_concurrent_execution():
    async def scenario():
        llm = FakeLLM([
            # The fake LLM requests two tools in the same response:
            response(calls=[
                tool_call("gpu_utilization"),
                tool_call("gpu_temperature"),
            ]),
            response(content="Monitoring complete"),
        ])
        executor = FakeExecutor()
        agent = Agent(llm, executor)

        await agent.run("Check GPU metrics")

        # This means both tools were active at the same time.
        assert executor.max_active == 2

        # The other assertion checks that both tools were executed, 
        # regardless of their order
        assert set(executor.executed) == {
            "gpu_utilization",
            "gpu_temperature",
        }

    asyncio.run(scenario())


def test_max_steps():
    # Because agent.run() is asynchronous, 
    # you need an event loop to execute it. 
    # asyncio.run() creates and manages that loop for the test.
    async def scenario():
        llm = FakeLLM([
            # Here, the LLM continually requests another tool:
            response(calls=[tool_call("gpu_status")])
            for _ in range(3)
        ])
        executor = FakeExecutor()

        # The test creates three such responses and sets:
        agent = Agent(llm, executor, max_steps=3)

        answer = await agent.run("Keep checking")

        # It verifies that the agent eventually 
        # stops instead of continuing indefinitely
        assert "maximum steps" in answer.lower()
        assert llm.calls == 3

    asyncio.run(scenario())
