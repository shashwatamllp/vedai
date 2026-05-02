import requests
import json
import sys
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

console = Console()

class OllamaOrchestrator:
    """
    Manages communication with the local Ollama service.
    Handles model verification, downloading, and inference.
    """
    BASE_URL = "http://localhost:11434/api"

    def __init__(self):
        self.check_connection()

    def check_connection(self):
        """Ensures Ollama is running locally."""
        try:
            response = requests.get(f"{self.BASE_URL}/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError
        except Exception:
            console.print("[bold red]Error:[/bold red] Ollama is not running! Please start Ollama first.")
            console.print("[yellow]Download from: https://ollama.com[/yellow]")
            sys.exit(1)

    def pull_model(self, model_name: str):
        """Pulls a model with a professional progress bar."""
        console.print(f"[bold cyan]Validating model:[/bold cyan] {model_name}...")
        
        # Check if already exists
        response = requests.get(f"{self.BASE_URL}/tags")
        models = [m['name'] for m in response.json().get('models', [])]
        
        if any(model_name in m for m in models):
            console.print(f"[green]✔ Model '{model_name}' is already installed.[/green]")
            return

        console.print(f"[yellow]Model '{model_name}' not found. Downloading...[/yellow]")
        
        url = f"{self.BASE_URL}/pull"
        data = {"name": model_name}
        
        with requests.post(url, json=data, stream=True) as response:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                transient=True,
            ) as progress:
                task = progress.add_task(f"Pulling {model_name}", total=100)
                
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        status = chunk.get("status", "")
                        completed = chunk.get("completed", 0)
                        total = chunk.get("total", 1)
                        
                        if total > 0:
                            percentage = (completed / total) * 100
                            progress.update(task, completed=completed, total=total)
                        
                        if status == "success":
                            progress.update(task, completed=total)

        console.print(f"[bold green]✔ Successfully installed {model_name}[/bold green]")

    def chat(self, model: str, prompt: str, system_prompt: str = ""):
        """Sends a message to the model and yields the streaming response."""
        url = f"{self.BASE_URL}/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True
        }

        try:
            with requests.post(url, json=payload, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        yield chunk.get("response", "")
                        if chunk.get("done", False):
                            break
        except Exception as e:
            console.print(f"\n[bold red]Inference Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    orch = OllamaOrchestrator()
    # Test with a small model
    # orch.pull_model("phi3:mini")
