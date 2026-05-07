import re
import logging
from typing import AsyncGenerator, Generator
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

    async def run(self, user_query: str, system_prompt: str) -> AsyncGenerator[str, None]:
        # Choose provider
        is_claude = self.model.startswith("claude-")
        
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
            
            try:
                if is_claude:
                    import anthropic
                    import os
                    client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
                    async with client.messages.stream(
                        model=self.model,
                        max_tokens=4096,
                        system=history[0]["content"],
                        messages=history[1:]
                    ) as stream:
                        async for text in stream.text_stream:
                            full_response += text
                            yield text
                else:
                    # Ollama (Local)
                    async for chunk in self.client.chat_async(self.model, history):
                        msg = chunk.get("message", {})
                        text = msg.get("content", "")
                        full_response += text
                        yield text
            except Exception as e:
                yield f"\n[bold red]Error communicating with Provider:[/bold red] {str(e)}"
                break

            # Parse JSON tool calls
            import json
            import re
            
            tool_called = False
            # Look for ```json ... ``` blocks
            json_blocks = re.findall(r"```json\s*(.*?)\s*```", full_response, re.DOTALL)
            for block in json_blocks:
                try:
                    tool_data = json.loads(block)
                    if "tool" in tool_data and "args" in tool_data:
                        tool_name = tool_data["tool"]
                        args_dict = tool_data["args"]
                        
                        yield f"\n\n[dim]🔧 VedAI is executing: {tool_name}...[/dim]\n"
                        
                        tool_output = self._execute_tool(tool_name, args_dict)
                        
                        # Add tool outputs to history to feed back to the LLM
                        history.append({"role": "assistant", "content": full_response})
                        
                        if tool_output.startswith("ERROR:"):
                            yield f"[dim red]Tool Error: {tool_output}[/dim red]\n"
                            history.append({"role": "user", "content": f"TOOL_ERROR: {tool_output}\nPlease self-correct and try again."})
                        else:
                            history.append({"role": "user", "content": f"TOOL_OUTPUT:\n{tool_output}"})
                        
                        tool_called = True
                        break # Only process one tool per step
                except json.JSONDecodeError:
                    continue
            
            if tool_called:
                yield f"\n[dim]🔄 Analyzing results (Step {current_step}/{max_steps})...[/dim]\n\n"
            else:
                # No valid tool call found, assume the model has provided the final answer.
                break

    def _build_prompt(self, history: list) -> str:
        flat = ""
        for msg in history:
            flat += f"{msg['role'].upper()}: {msg['content']}\n"
        flat += "ASSISTANT: "
        return flat

    def _execute_tool(self, name: str, args: dict) -> str:
        try:
            if name == "list_files":
                return self.tools.list_files(args.get("path", "."))
            elif name == "read_file":
                return self.tools.read_file(args.get("file_path", ""))
            elif name == "write_file":
                return self.tools.write_file(args.get("file_path", ""), args.get("content", ""))
            elif name == "execute_shell":
                res = self.tools.execute_shell(args.get("command", ""))
                # Self-correction: check if shell command failed
                if "Exit Code:" in res and not "Exit Code: 0" in res:
                    return f"ERROR: Command failed.\n{res}"
                return res
            elif name == "get_project_tree":
                return self.tools.get_project_tree()
            elif name == "search_code":
                return self.tools.search_code(args.get("query", ""))
            else:
                return f"ERROR: Tool {name} not found."
        except Exception as e:
            return f"ERROR: Exception executing {name}: {str(e)}"
