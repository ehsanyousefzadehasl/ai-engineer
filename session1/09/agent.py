
import asyncio


class Agent:
    def __init__(self, llm, tool_executor, max_steps=5):
        self.llm = llm
        self.executor = tool_executor
        self.max_steps = max_steps

    async def run(self, request):
        tools = await self.executor.discover()

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a GPU infrastructure assistant. "
                    "Use tools to answer GPU monitoring questions. "
                    "For memory feasibility checks, call gpu_status "
                    "before estimate_training_fit. "
                    "GPU measurements are mocked."
                ),
            },
            {"role": "user", "content": request},
        ]

        for step in range(self.max_steps):
            print(f"\nAgent step {step + 1}")

            response = await self.llm.chat(messages, tools)
            messages.append(response.message)

            calls = response.message.tool_calls or []

            if not calls:
                return response.message.content

            results = await asyncio.gather(
                *(self.executor.execute(call) for call in calls)
            )

            messages.extend(results)

        return "Agent stopped: maximum steps reached."
