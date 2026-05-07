from backend.core.ollama import OllamaClient
from backend.agents.prompts import SYSTEM_PROMPT


class SelfCorrector:
    """
    SelfCorrector: When Verifier reports errors, this agent
    sends the error context back to the LLM and asks it to
    produce a corrected plan.
    
    This is the core of the autonomous self-healing loop.
    """

    def __init__(self):
        self.llm = OllamaClient()

    async def fix(
        self,
        original_task: str,
        failed_plan: str,
        errors: list
    ) -> str:
        error_text = "\n".join(errors)

        prompt = f"""
{SYSTEM_PROMPT}

## Original Task:
{original_task}

## Your Previous Plan (which FAILED):
{failed_plan}

## Errors Encountered:
{error_text}

## Your Job:
Analyze the errors above carefully.
Produce a CORRECTED plan that fixes these specific errors.
Use the same JSON action block format as before.
Do NOT repeat the same mistake.
"""
        return await self.llm.generate(prompt)
