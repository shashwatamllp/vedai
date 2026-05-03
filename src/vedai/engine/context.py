import os
from pathlib import Path
from typing import List
import pathspec

from vedai.engine.graph import SymbolGraph

class ContextManager:
    """
    Enterprise-grade project context management with .gitignore support and Symbol Graph.
    """
    DEFAULT_EXCLUDES = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build'}
    ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.html', '.css', '.md', '.json', '.txt', '.c', '.cpp', '.h', '.go', '.rs'}

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.spec = self._load_gitignore()
        self.graph = SymbolGraph(root_path)

    def _load_gitignore(self) -> pathspec.PathSpec:
        gitignore_path = self.root_path / ".gitignore"
        patterns = list(self.DEFAULT_EXCLUDES)
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                patterns.extend(f.readlines())
        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    def scan(self) -> List[Path]:
        files = []
        for root, dirs, filenames in os.walk(self.root_path):
            rel_root = Path(root).relative_to(self.root_path)
            
            # Prune directories based on gitignore
            dirs[:] = [d for d in dirs if not self.spec.match_file(str(rel_root / d))]
            
            for f in filenames:
                path = rel_root / f
                if not self.spec.match_file(str(path)) and path.suffix.lower() in self.ALLOWED_EXTENSIONS:
                    files.append(self.root_path / path)
        return files

    def build_context(self) -> str:
        files = self.scan()
        context = [f"Project Root: {self.root_path.name}\nFiles discovered: {len(files)}\n"]
        
        for f in files:
            try:
                if f.stat().st_size < 100000: # 100KB limit
                    rel_path = f.relative_to(self.root_path)
                    content = f.read_text(encoding='utf-8', errors='ignore')
                    context.append(f"--- File: {rel_path} ---\n{content}\n")
            except Exception:
                continue
        return "\n".join(context)
