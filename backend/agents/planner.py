from backend.core.ollama import OllamaClient
from backend.agents.prompts import (
    SYSTEM_PROMPT
)


class Planner:

    def __init__(self):

        self.llm = OllamaClient()

    async def create_plan(
        self,
        task: str,
        context: str
    ):

        prompt = f"""

{SYSTEM_PROMPT}

Current Context:

{context}

Task:

{task}

Create a detailed execution plan.

"""

        return await self.llm.generate(
            prompt
        )
