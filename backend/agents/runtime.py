from backend.core.state import AgentState

from backend.memory.context_memory import (
    ContextMemory
)

from backend.agents.planner import (
    Planner
)

from backend.agents.executor import (
    Executor
)


class RuntimeAgent:

    def __init__(self):

        self.memory = ContextMemory()

        self.planner = Planner()

        self.executor = Executor()

    async def run(
        self,
        task: str
    ):

        state = AgentState(
            task=task
        )

        context = self.memory.build_context()

        plan = await self.planner.create_plan(
            task=task,
            context=context
        )

        state.actions.append(
            {
                "plan": plan
            }
        )

        result = await self.executor.execute(
            plan
        )

        state.outputs.append(
            result
        )

        self.memory.add(
            result
        )

        state.completed = True

        return {
            "task": task,
            "plan": plan,
            "result": result,
            "memory": self.memory.latest()
        }
