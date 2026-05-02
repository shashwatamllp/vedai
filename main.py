import sys
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt

from hardware_engine import HardwareEngine
from model_orchestrator import OllamaOrchestrator
from context_engine import ContextEngine

console = Console()

class VedAIApp:
    def __init__(self):
        self.hardware = HardwareEngine()
        self.orchestrator = OllamaOrchestrator()
        self.context = ContextEngine()
        self.current_model = self.hardware.get_recommended_model()

    def startup(self):
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]VED-AI: HIGH-LEVEL LOCAL DEV ASSISTANT[/bold cyan]\n"
            "[italic white]Advanced Project Intelligence Engine[/italic white]",
            border_style="blue"
        ))
        
        self.hardware.display_report()
        self.orchestrator.pull_model(self.current_model)
        
        console.print(f"\n[bold green]System Ready![/bold green] Using [bold yellow]{self.current_model}[/bold yellow]")
        console.print("[dim]Type '/exit' to quit, '/refresh' to rescanning files, '/model' to change model[/dim]\n")

    def run(self):
        self.startup()
        
        while True:
            try:
                user_input = Prompt.ask("[bold magenta]User[/bold magenta]")
                
                if user_input.lower() in ['/exit', 'exit', 'quit']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if user_input.lower() == '/refresh':
                    with console.status("[bold blue]Refreshing project context..."):
                        project_context = self.context.get_project_summary()
                    console.print("[green]Context updated![/green]")
                    continue

                if user_input.lower() == '/model':
                    new_model = Prompt.ask("Enter model name (e.g. llama3, mistral, codellama)")
                    self.orchestrator.pull_model(new_model)
                    self.current_model = new_model
                    console.print(f"[green]Switched to {new_model}[/green]")
                    continue

                # Prepare System Prompt with Context
                with console.status("[bold blue]Analyzing project..."):
                    project_context = self.context.get_project_summary()
                
                system_prompt = (
                    "You are VedAI, a high-level senior software engineer AI. "
                    "You run locally on the user's machine. "
                    "Below is the context of the user's current project. "
                    "Use this information to answer precisely and help with coding tasks.\n\n"
                    f"{project_context}"
                )

                # Streaming Response
                console.print("\n[bold cyan]VedAI:[/bold cyan]")
                full_response = ""
                
                with Live(Markdown(""), refresh_per_second=10) as live:
                    for chunk in self.orchestrator.chat(self.current_model, user_input, system_prompt):
                        full_response += chunk
                        live.update(Markdown(full_response))
                
                console.print("\n" + "─" * console.width + "\n")

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
                continue

if __name__ == "__main__":
    app = VedAIApp()
    app.run()
