import json
import re
from backend.tools.filesystem import FileSystemTool
from backend.tools.terminal import TerminalTool


class Executor:
    """
    Real Executor: Parses the Planner's output and actually
    runs file writes and terminal commands.
    
    The Planner is expected to output JSON action blocks like:
    
    ```json
    {
        "action": "write_file",
        "path": "main.py",
        "content": "print('hello')"
    }
    ```
    or
    ```json
    {
        "action": "run_command",
        "command": ["python", "main.py"]
    }
    ```
    """

    def __init__(self):
        self.fs = FileSystemTool()
        self.terminal = TerminalTool()
        self.results = []

    async def execute(self, plan: str) -> dict:
        self.results = []
        actions = self._parse_actions(plan)

        if not actions:
            # No structured actions found — return the plan as-is (pure text response)
            return {
                "status": "completed",
                "actions_taken": [],
                "output": plan,
                "errors": []
            }

        errors = []
        for action in actions:
            result = await self._run_action(action)
            self.results.append(result)
            if result.get("error"):
                errors.append(result["error"])

        return {
            "status": "failed" if errors else "completed",
            "actions_taken": self.results,
            "output": self._format_output(),
            "errors": errors
        }

    def _parse_actions(self, text: str) -> list:
        """Extract JSON action blocks from the planner's text output."""
        pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
        matches = re.findall(pattern, text)
        actions = []
        for match in matches:
            try:
                actions.append(json.loads(match))
            except json.JSONDecodeError:
                pass
        return actions

    async def _run_action(self, action: dict) -> dict:
        action_type = action.get("action", "")

        if action_type == "write_file":
            path = action.get("path", "")
            content = action.get("content", "")
            try:
                self.fs.write(path, content)
                return {"action": f"write_file: {path}", "status": "✅ Created", "error": None}
            except Exception as e:
                return {"action": f"write_file: {path}", "status": "❌ Failed", "error": str(e)}

        elif action_type == "read_file":
            path = action.get("path", "")
            content = self.fs.read(path)
            return {"action": f"read_file: {path}", "status": "✅ Read", "output": content, "error": None}

        elif action_type == "run_command":
            command = action.get("command", [])
            if isinstance(command, str):
                command = command.split()
            try:
                result = self.terminal.execute(command)
                ok = result["returncode"] == 0
                return {
                    "action": f"run: {' '.join(command)}",
                    "status": "✅ Success" if ok else "❌ Error",
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "returncode": result["returncode"],
                    "error": result["stderr"] if not ok else None
                }
            except Exception as e:
                return {"action": f"run: {command}", "status": "❌ Blocked/Failed", "error": str(e)}

        else:
            return {"action": action_type or "unknown", "status": "⚠️ Unknown action", "error": None}

    def _format_output(self) -> str:
        lines = []
        for r in self.results:
            lines.append(f"{r['status']} {r['action']}")
            if r.get("stdout"):
                lines.append(f"  OUTPUT: {r['stdout'].strip()}")
            if r.get("error"):
                lines.append(f"  ERROR: {r['error'].strip()}")
        return "\n".join(lines)
