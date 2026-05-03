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
from vedai.engine.agent import AgentLoop
from vedai.engine.tools import ToolEngine
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
    
    tools = ToolEngine()
    agent = AgentLoop(client, tools, selected_model)
    
    # Check if model is pulled
    installed = client.get_installed_models()
    if selected_model not in installed and (selected_model + ":latest") not in installed:
        console.print(f"[yellow]📥 Model '{selected_model}' not found. Initializing High-Speed Pull...[/yellow]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            transient=False
        ) as progress:
            task = progress.add_task(f"Downloading {selected_model}", total=100)
            try:
                for chunk in client.pull_model(selected_model):
                    status = chunk.get("status", "")
                    completed = chunk.get("completed", 0)
                    total = chunk.get("total", 0)
                    
                    if total > 0:
                        progress.update(task, completed=completed, total=total, description=f"Pulling: {status}")
                    else:
                        progress.update(task, description=f"Status: {status}")
                
                progress.update(task, description="✅ Download Complete!")
            except Exception as e:
                console.print(f"[red]Failed to pull model: {e}[/red]")
                # Fallback to background pull if progress fails
                subprocess.run(["ollama", "pull", selected_model], capture_output=True)

    layout = VedUI.get_layout()
    VedUI.update_header(layout)
    VedUI.update_sidebar(layout, hw.specs, selected_model)
    VedUI.update_main(layout, "Welcome to VedAI Prime. Type your query below.")
    # Optimized Chat Loop (Stable & Fast)
    try:
        while True:
            console.print("\n" + "="*50)
            query = console.input("[bold cyan]User:[/bold cyan] ")
            
            if query.lower() in ["exit", "quit"]:
                break
                
            # Smart Context (Optimized)
            with console.status("[bold yellow]VedAI is thinking...[/bold yellow]"):
                files = ctx_mgr.scan()
                ctx_mgr.graph.index_project(files)
                
                system_prompt = get_system_prompt(ctx_mgr)
                words = query.split()
                graph_context = str(ctx_mgr.graph.get_context_for_agent(words))
                full_system_prompt = str(system_prompt)[:4000] + "\n" + graph_context
                
                console.print("\n[bold green]VedAI Prime:[/bold green]")
                response_text = ""
                for chunk in agent.run(query, full_system_prompt):
                    response_text += chunk
                    # Simple streaming print for stability
                    console.print(chunk, end="")
                
                console.print("\n" + "-"*50)

    except KeyboardInterrupt:
        console.print("\n[yellow]Session Ended.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]CRITICAL ERROR:[/bold red] {e}")
        input("\nPress Enter to exit...")

@app.command()
def doctor():
    """Run a full system diagnostic and hardware check."""
    VedUI.banner()
    hw = HardwareEngine()
    VedUI.hardware_report(hw.specs, hw.get_recommended_model())
    console.print("[green]Diagnostic complete. System is ready for Local AI.[/green]")

if __name__ == "__main__":
    app()
