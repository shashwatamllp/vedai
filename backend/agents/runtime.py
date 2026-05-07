from backend.core.state import AgentState
from backend.memory.context_memory import ContextMemory
from backend.agents.planner import Planner
from backend.agents.executor import Executor
from backend.agents.verifier import Verifier
from backend.agents.self_corrector import SelfCorrector


MAX_RETRIES = 3  # Max self-correction attempts


class RuntimeAgent:
    """
    The Orchestrator.
    
    Full autonomous loop:
    1. Planner: think and produce a plan with action blocks
    2. Executor: actually run the actions (write files, run commands)
    3. Verifier: check if execution succeeded
    4. SelfCorrector: if failed, send errors back to LLM and fix
    5. Repeat up to MAX_RETRIES times
    """

    def __init__(self):
        self.memory = ContextMemory()
        self.planner = Planner()
        self.executor = Executor()
        self.verifier = Verifier()
        self.corrector = SelfCorrector()

    async def run(self, task: str):
        state = AgentState(task=task)
        context = self.memory.build_context()

        # --- Step 1: Plan ---
        plan = await self.planner.create_plan(task=task, context=context)
        state.actions.append({"step": "plan", "content": plan})

        current_plan = plan
        attempt = 0

        while attempt < MAX_RETRIES:
            attempt += 1

            # --- Step 2: Execute ---
            exec_result = await self.executor.execute(current_plan)
            state.outputs.append({"attempt": attempt, "result": exec_result})

            # --- Step 3: Verify ---
            verification = self.verifier.verify(exec_result)

            if verification["passed"]:
                # SUCCESS
                state.completed = True
                self.memory.add({
                    "task": task,
                    "plan": current_plan,
                    "result": exec_result["output"],
                    "status": "success"
                })
                return {
                    "task": task,
                    "plan": current_plan,
                    "execution": exec_result,
                    "verification": verification,
                    "attempts": attempt,
                    "status": "success"
                }
            else:
                # FAILED — try to self-correct
                state.errors.extend(verification["errors"])

                if attempt < MAX_RETRIES:
                    # Ask LLM to fix
                    corrected_plan = await self.corrector.fix(
                        original_task=task,
                        failed_plan=current_plan,
                        errors=verification["errors"]
                    )
                    current_plan = corrected_plan
                    state.actions.append({
                        "step": f"self_correction_attempt_{attempt}",
                        "content": corrected_plan
                    })

        # All retries exhausted
        state.completed = False
        return {
            "task": task,
            "plan": current_plan,
            "execution": exec_result,
            "verification": verification,
            "attempts": attempt,
            "status": "failed",
            "errors": state.errors
        }
