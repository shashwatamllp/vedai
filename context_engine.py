import os
from pathlib import Path
from typing import List, Dict

class ContextEngine:
    """
    Intelligently scans the current project directory to provide AI context.
    """
    EXCLUDED_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build'}
    ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.html', '.css', '.md', '.json', '.txt', '.c', '.cpp', '.h'}

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()

    def get_project_summary(self) -> str:
        """Returns a string representation of the project structure and key file contents."""
        files_found = self._scan_files()
        
        context_parts = ["### PROJECT CONTEXT ###\n"]
        context_parts.append(f"Root Directory: {self.root_dir.name}\n")
        context_parts.append("File Structure:")
        
        for file_path in files_found:
            rel_path = file_path.relative_to(self.root_dir)
            context_parts.append(f"- {rel_path}")

        context_parts.append("\n### FILE CONTENTS ###")
        
        # We only read small files or key files to avoid hitting context limits
        for file_path in files_found:
            try:
                # Basic logic: Only read files smaller than 50KB for context
                if file_path.stat().st_size < 50000:
                    rel_path = file_path.relative_to(self.root_dir)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context_parts.append(f"\n--- File: {rel_path} ---\n{content}\n")
            except Exception:
                continue
                
        return "\n".join(context_parts)

    def _scan_files(self) -> List[Path]:
        """Recursively scans the directory for relevant code files."""
        relevant_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.ALLOWED_EXTENSIONS:
                    relevant_files.append(file_path)
        
        return relevant_files

if __name__ == "__main__":
    engine = ContextEngine()
    print(engine.get_project_summary())
