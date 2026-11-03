
from ollama import AsyncClient


class OllamaLLM:
    def __init__(self, model="qwen3:4b"):
        self.client = AsyncClient()
        self.model = model

    async def chat(self, messages, tools):
        return await self.client.chat(
            model=self.model,
            messages=messages,
            tools=tools,
        )
