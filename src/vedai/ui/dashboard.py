from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.live import Live
import datetime

console = Console()

class VedUI:
    @staticmethod
    def get_layout():
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="sidebar", size=40),
            Layout(name="main", ratio=1)
        )
        return layout

    @staticmethod
    def update_header(layout):
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        title = Text.assemble(
            (" 🌌 ", "cyan"),
            ("VED-AI ", "bold magenta"),
            ("PRIME", "bold white on magenta"),
            ("  ", "white"),
            ("Shashwatam Eco-Chie Creations LLP", "italic dim white")
        )
        
        grid.add_row(
            title,
            Text(datetime.datetime.now().strftime("%H:%M:%S"), style="bold cyan")
        )
        
        layout["header"].update(Panel(grid, border_style="bright_blue", title="[bold blue]System Header[/bold blue]"))

    @staticmethod
    def update_sidebar(layout, specs, model):
        table = Table.grid(padding=1)
        table.add_column(style="bold cyan")
        table.add_column(style="magenta")
        
        table.add_row("🖥️  OS", specs.os_name)
        table.add_row("⚙️  CPU", f"{specs.cpu_cores} Cores")
        table.add_row("💾 RAM", f"{specs.total_ram_gb} GB")
        table.add_row("🎮 GPU", specs.gpu_name or "CPU Mode")
        table.add_row("⚡ VRAM", f"{specs.vram_gb} GB")
        table.add_row("🤖 ENGINE", f"[bold green]{model}[/bold green]")
        
        layout["sidebar"].update(Panel(
            Align.center(table, vertical="middle"),
            title="[bold yellow]Hardware Core[/bold yellow]",
            border_style="bright_magenta"
        ))

    @staticmethod
    def update_main(layout, content):
        layout["main"].update(Panel(
            content,
            title="[bold green]Intelligence Feed[/bold green]",
            border_style="bright_green"
        ))

    @staticmethod
    def update_footer(layout, status="Ready"):
        text = Text.assemble(
            (" STATUS: ", "bold white"),
            (f" {status} ", "bold black on green" if "Ready" in status else "bold black on yellow"),
            ("  |  ", "dim"),
            ("/chat ", "cyan"), ("/doctor ", "magenta"), ("/exit ", "red")
        )
        layout["footer"].update(Align.center(text, vertical="middle"))

    @staticmethod
    def banner():
        # Fallback for simple banner
        console.print(Panel.fit(
            "[bold cyan]VED-AI PRIME[/bold cyan]\n"
            "[dim]Powered by Shashwatam Eco-Chie Creations[/dim]",
            border_style="blue"
        ))
