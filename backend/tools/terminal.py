import subprocess


SAFE_COMMANDS = [
    "python",
    "git",
    "npm",
    "pytest",
    "pip"
]


class TerminalTool:

    @staticmethod
    def execute(command: list):

        if command[0] not in SAFE_COMMANDS:
            raise Exception(
                f"Blocked command: {command[0]}"
            )

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
