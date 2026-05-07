class Verifier:
    """
    Verifier: Checks the output of the Executor.
    - If all actions completed successfully → passes
    - If any action failed (non-zero exit, write error) → reports errors
    """

    def verify(self, execution_result: dict) -> dict:
        errors = execution_result.get("errors", [])
        actions = execution_result.get("actions_taken", [])
        
        failed_actions = [
            a for a in actions
            if "❌" in a.get("status", "")
        ]

        if not errors and not failed_actions:
            return {
                "passed": True,
                "summary": "✅ All steps completed successfully.",
                "errors": []
            }
        
        error_summary = []
        for a in failed_actions:
            error_summary.append(
                f"Action '{a['action']}' failed: {a.get('error', 'Unknown error')}"
            )

        return {
            "passed": False,
            "summary": f"❌ {len(error_summary)} step(s) failed.",
            "errors": error_summary
        }
