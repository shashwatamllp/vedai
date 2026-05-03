import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ToolEngine:
    """
    Executes real-world actions on the system for the VedAI Agent.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()

    def list_files(self, path: str = ".") -> str:
        """Lists files in a directory."""
        try:
            target = (self.root_dir / path).resolve()
            files = os.listdir(target)
            return "\n".join(files)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def read_file(self, file_path: str) -> str:
        """Reads the content of a file."""
        try:
            target = (self.root_dir / file_path).resolve()
            return target.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str) -> str:
        """Writes content to a file, creating directories if needed."""
        try:
            target = (self.root_dir / file_path).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def execute_shell(self, command: str) -> str:
        """Executes a shell command and returns output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.root_dir),
                timeout=30
            )
            output = result.stdout + result.stderr
            return f"Exit Code: {result.returncode}\nOutput:\n{output}"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def get_project_tree(self) -> str:
        """Returns a tree view of the entire project."""
        tree = []
        for root, dirs, files in os.walk(self.root_dir):
            if '.git' in dirs: dirs.remove('.git')
            if '__pycache__' in dirs: dirs.remove('__pycache__')
            level = Path(root).relative_to(self.root_dir).parts
            indent = '  ' * len(level)
            tree.append(f"{indent}📁 {os.path.basename(root)}/")
            for f in files:
                tree.append(f"{indent}  📄 {f}")
        return "\n".join(tree)

    def search_code(self, query: str) -> str:
        """Searches for a string across all project files."""
        results = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css', '.md', '.toml')):
                    path = Path(root) / file
                    try:
                        content = path.read_text(encoding='utf-8')
                        if query.lower() in content.lower():
                            results.append(str(path.relative_to(self.root_dir)))
                    except: pass
        return "Found in:\n" + "\n".join(results) if results else "No matches found."

    def get_tool_definitions(self) -> str:
        """Returns the prompt-friendly definitions of available tools."""
        return """
Available Tools:
1. `list_files(path)`: List directory contents.
2. `read_file(path)`: Read file content.
3. `write_file(path, content)`: Write/Over-write file content.
4. `execute_shell(command)`: Run a terminal command.
5. `get_project_tree()`: Get entire project structure.
6. `search_code(query)`: Search for text across codebase.

To use a tool, respond in this format:
THOUGHT: [Reasoning]
TOOL: tool_name(arguments)
"""
