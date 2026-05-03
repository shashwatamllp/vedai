import typer
import logging
import subprocess
import re
import os
import psutil
import time
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
    
    # [AUTONOMOUS PATH FIX] Ensure Ollama knows about our big storage drive
    for part in psutil.disk_partitions():
        potential_models = os.path.join(part.mountpoint, "VedAI_System", "Models")
        if os.path.exists(potential_models):
            os.environ["OLLAMA_MODELS"] = potential_models
            console.print(f"[dim]Auto-detected model storage: {potential_models}[/dim]")
            break

    selected_model = model or hw.get_recommended_model()
    VedUI.hardware_report(hw.specs, selected_model)
    
    tools = ToolEngine()
    agent = AgentLoop(client, tools, selected_model)
    
    # Check if model is pulled
    installed = client.get_installed_models()
    if selected_model not in installed and (selected_model + ":latest") not in installed:
        console.print(f"[yellow]📥 Model '{selected_model}' not found. Initializing Resilient Pull...[/yellow]")
        try:
            # Fallback list in case specific version fails
            models_to_try = [selected_model, "qwen2.5-coder:latest", "phi3:mini"]
            success = False
            
            for m in models_to_try:
                console.print(f"[dim]Trying to pull {m}...[/dim]")
                process = subprocess.Popen(
                    ["ollama", "pull", m],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                for line in process.stdout:
                    # Deep ANSI cleaning for cleaner terminal output
                    clean_line = re.sub(r'(\x1b\[|\?|1G|\[K|\[?25l|\[?25h|\[?2026h|\[?2026l)', '', line).strip()
                    if clean_line and any(k in clean_line.lower() for k in ["pulling", "verifying", "downloading"]):
                        console.print(f"[blue]Status:[/blue] {clean_line}")
                
                process.wait()
                if process.returncode == 0:
                    success = True
                    selected_model = m # Update to the one that worked
                    console.print(f"✅ Model {m} Pull Successful!")
                    break
            
            if not success:
                console.print("[red]All pull attempts failed. Manual action required.[/red]")
                console.print(f"👉 Please run this in a NEW terminal: [bold]ollama pull {selected_model}[/bold]")
                input("Press Enter once you have started the download manually...")
        except Exception as e:
            console.print(f"[red]Error during pull: {e}[/red]")

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
def studio():
    """Launch the Premium VedAI Web Studio."""
    import webbrowser
    from vedai.server import app
    import uvicorn

    console.print("\n" + "="*50)
    console.print("🚀 [bold cyan]LAUNCHING VED-AI PREMIUM STUDIO[/bold cyan]")
    console.print("📍 URL: [bold green]http://127.0.0.1:8000[/bold green]")
    console.print("👉 [dim]If the browser doesn't open, copy the URL above into Chrome.[/dim]")
    console.print("="*50 + "\n")

    try:
        # Open browser slightly after server starts (simulated)
        def open_browser():
            time.sleep(2)
            webbrowser.open("http://127.0.0.1:8000")
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Run server in main thread to see ALL errors
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        console.print(f"\n[bold red]STUDIO ERROR:[/bold red] {e}")
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
