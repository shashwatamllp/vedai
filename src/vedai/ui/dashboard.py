from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class VedUI:
    @staticmethod
    def banner():
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]VED-AI: ENTERPRISE EDITION[/bold cyan]\n"
            "[bold white]Ved4u by Shashwatam Eco-Chie Creations LLP[/bold white]\n"
            "[blue]Web:[/blue] www.vedsaas.com | [blue]Support:[/blue] support@vedsaas.com",
            border_style="blue",
            padding=(1, 2)
        ))

    @staticmethod
    def hardware_report(specs, model):
        table = Table(title="[bold yellow]System Diagnostic[/bold yellow]", border_style="dim")
        table.add_column("Resource", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Operating System", specs.os_name)
        table.add_row("Processor Cores", str(specs.cpu_cores))
        table.add_row("Memory (RAM)", f"{specs.total_ram_gb} GB")
        table.add_row("GPU (VRAM)", f"{specs.gpu_name or 'None'} ({specs.vram_gb} GB)")
        
        console.print(table)
        console.print(f"\n[green]Optimized Engine:[/green] [bold white]{model}[/bold white]\n")
