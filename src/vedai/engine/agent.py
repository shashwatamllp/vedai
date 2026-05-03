import re
import logging
from typing import Generator
from rich.console import Console
from vedai.engine.ollama import OllamaClient
from vedai.engine.tools import ToolEngine

logger = logging.getLogger(__name__)
console = Console()

class AgentLoop:
    """
    The Thinking Loop that allows VedAI to use tools autonomously.
    """
    def __init__(self, client: OllamaClient, tools: ToolEngine, model: str):
        self.client = client
        self.tools = tools
        self.model = model

    def run(self, user_query: str, system_prompt: str) -> Generator[str, None, None]:
        history = [
            {"role": "system", "content": system_prompt + "\n" + self.tools.get_tool_definitions() + 
             "\nINSTRUCTIONS: You are a local autonomous coding agent. Use tools to explore the codebase and fulfill requests. "
             "Always use THOUGHT before using a TOOL. If you have the answer, provide it directly without TOOL calls."},
            {"role": "user", "content": user_query}
        ]
        
        max_steps = 10
        current_step = 0
        
        while current_step < max_steps:
            current_step += 1
            full_response = ""
            
            # Get response from LLM using chat API (structured messages)
            try:
                for chunk in self.client.chat(self.model, history):
                    text = chunk.get("response", "")
                    full_response += text
                    yield text
            except Exception as e:
                yield f"\n[bold red]Error communicating with Ollama:[/bold red] {str(e)}"
                break

            # Parse tool calls: TOOL: tool_name(args)
            tool_match = re.search(r"TOOL:\s*(\w+)\((.*)\)", full_response)
            
            if tool_match:
                tool_name = tool_match.group(1)
                args_str = tool_match.group(2)
                
                console.print(f"\n[bold yellow]Agent Action:[/bold yellow] {tool_name}({args_str})")
                
                # Execute tool
                tool_output = self._execute_tool(tool_name, args_str)
                console.print(f"[dim]Tool Output received ({len(tool_output)} chars)[/dim]")
                
                # Add to history and continue loop
                history.append({"role": "assistant", "content": full_response})
                history.append({"role": "user", "content": f"TOOL OUTPUT: {tool_output}"})
                yield f"\n\n--- Step {current_step} complete. Analyzing output... ---\n\n"
            else:
                # No tool call found, assume final answer
                break

    def _build_prompt(self, history: list) -> str:
        # Convert history list to a flat string prompt for the model
        flat = ""
        for msg in history:
            flat += f"{msg['role'].upper()}: {msg['content']}\n"
        flat += "ASSISTANT: "
        return flat

    def _execute_tool(self, name: str, args_str: str) -> str:
        try:
            # Very basic argument parsing (supporting strings and simple args)
            # In a real enterprise app, we'd use a proper parser or JSON
            if name == "list_files":
                return self.tools.list_files(args_str.strip("'\" "))
            elif name == "read_file":
                return self.tools.read_file(args_str.strip("'\" "))
            elif name == "write_file":
                # Splitting file and content might be tricky with regex
                parts = args_str.split(",", 1)
                if len(parts) == 2:
                    return self.tools.write_file(parts[0].strip("'\" "), parts[1].strip("'\" "))
                return "Error: write_file requires path and content."
            elif name == "execute_shell":
                return self.tools.execute_shell(args_str.strip("'\" "))
            else:
                return f"Error: Tool {name} not found."
        except Exception as e:
            return f"Error executing {name}: {str(e)}"
