import typer
import logging
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

from vedai.engine.hardware import HardwareEngine
from vedai.engine.ollama import OllamaClient
from vedai.engine.context import ContextManager
from vedai.ui.dashboard import VedUI

app = typer.Typer(help="VedAI: High-level Local AI Assistant")
console = Console()

def get_system_prompt(ctx: ContextManager):
    project_context = ctx.build_context()
    return (
        "You are VedAI, a high-level senior software engineer AI developed by Shashwatam Eco-Chie Creations LLP. "
        "You run locally on the user's machine via Ved4u. "
        "Below is the full context of the user's current project. "
        "Analyze it and provide expert assistance.\n\n"
        f"{project_context}"
    )

@app.command()
def chat(
    model: Optional[str] = typer.Option(None, help="Specific model to use"),
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Force context refresh")
):
    """Start an interactive project-aware chat session."""
    VedUI.banner()
    
    hw = HardwareEngine()
    client = OllamaClient()
    ctx_mgr = ContextManager()
    
    selected_model = model or hw.get_recommended_model()
    VedUI.hardware_report(hw.specs, selected_model)
    
    # Check if model is pulled
    if selected_model not in client.get_installed_models():
        console.print(f"[yellow]Model '{selected_model}' not found. Pulling...[/yellow]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), transient=True) as progress:
            task = progress.add_task(f"Pulling {selected_model}", total=100)
            for chunk in client.pull_model(selected_model):
                completed = chunk.get("completed", 0)
                total = chunk.get("total", 1)
                if total > 0:
                    progress.update(task, completed=completed, total=total)

    layout = VedUI.get_layout()
    VedUI.update_header(layout)
    VedUI.update_sidebar(layout, hw.specs, selected_model)
    VedUI.update_main(layout, "Welcome to VedAI Prime. Type your query below.")
    VedUI.update_footer(layout, "System Online")

    with Live(layout, refresh_per_second=4, screen=True):
        while True:
            VedUI.update_footer(layout, "Waiting for Input")
            query = typer.prompt("User")
            if query.lower() in ["exit", "quit"]:
                break
                
            system_prompt = get_system_prompt(ctx_mgr)
            VedUI.update_footer(layout, "Agent Thinking...")
            
            response_text = ""
            for chunk in agent.run(query, system_prompt):
                response_text += chunk
                VedUI.update_main(layout, Markdown(response_text))
            
            VedUI.update_footer(layout, "Response Ready")
            # Small pause to let the user see the "Response Ready" state
            import time
            time.sleep(1)

@app.command()
def doctor():
    """Run a full system diagnostic and hardware check."""
    VedUI.banner()
    hw = HardwareEngine()
    VedUI.hardware_report(hw.specs, hw.get_recommended_model())
    console.print("[green]Diagnostic complete. System is ready for Local AI.[/green]")

if __name__ == "__main__":
    app()
