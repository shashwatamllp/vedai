import sqlite3
import logging
from pathlib import Path
from tree_sitter_languages import get_language, get_parser

logger = logging.getLogger(__name__)

class SymbolGraph:
    """
    VedAI Bridge Graph: Intelligent Symbol Indexing using Tree-Sitter.
    Maps functions, classes, and calls to provide deep context to local LLMs.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.db_path = self.root_dir / ".vedai" / "symbols.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    file_path TEXT,
                    line_start INTEGER,
                    line_end INTEGER,
                    signature TEXT,
                    UNIQUE(name, file_path, line_start)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_name ON symbols(name)")

    def index_project(self, files: list):
        """Scans and indexes all project files silently."""
        for file_path in files:
            try:
                self.index_file(file_path)
            except:
                pass

    def index_file(self, file_path: Path):
        ext = file_path.suffix
        lang_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.go': 'go', '.rs': 'rust'}
        
        if ext not in lang_map:
            return

        lang_name = lang_map[ext]
        language = get_language(lang_name)
        parser = get_parser(lang_name)
        
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = parser.parse(bytes(content, "utf8"))
        
        # Simple query to find function/class definitions
        # This can be expanded with more complex Tree-Sitter queries
        query_scm = """
        (function_definition name: (identifier) @name) @func
        (class_definition name: (identifier) @name) @class
        """
        if lang_name in ['javascript', 'typescript']:
            query_scm = """
            (function_declaration name: (identifier) @name) @func
            (class_declaration name: (identifier) @name) @class
            (method_definition name: (property_identifier) @name) @method
            """

        try:
            query = language.query(query_scm)
            captures = query.captures(tree.root_node)
        except:
            return

        with sqlite3.connect(self.db_path) as conn:
            for node, tag in captures:
                if tag in ['name', 'property_identifier']: continue # We want the definitions
                
                # Extract name based on tag
                name_node = node.child_by_field_name('name')
                if not name_node: continue
                
                name = content[name_node.start_byte:name_node.end_byte]
                symbol_type = tag
                
                conn.execute("""
                    INSERT OR REPLACE INTO symbols (name, type, file_path, line_start, line_end, signature)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    name, 
                    symbol_type, 
                    str(file_path.relative_to(self.root_dir)),
                    node.start_point[0] + 1,
                    node.end_point[0] + 1,
                    content[node.start_byte:node.end_byte].split('\n')[0] # First line as signature
                ))

    def search_symbol(self, query: str) -> list:
        """Finds symbols matching the query name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT name, type, file_path, line_start, signature FROM symbols WHERE name LIKE ?", 
                (f"%{query}%",)
            )
            return cursor.fetchall()

    def get_context_for_agent(self, detected_symbols: list) -> str:
        """Builds a context string from detected symbols for the LLM prompt."""
        if not detected_symbols:
            return ""
            
        context = ["\n[SYMBOL GRAPH CONTEXT]"]
        has_results = False
        for sym in detected_symbols:
            if len(sym) < 3: continue # Skip very short words
            results = self.search_symbol(sym)
            for r in results:
                has_results = True
                context.append(f"- {r[1].upper()} '{r[0]}' in {r[2]} (Line {r[3]}): `{r[4]}`")
        
        return "\n".join(context) if has_results else ""
