import psutil
import platform
import subprocess
import logging
from dataclasses import dataclass
from typing import Optional

# Professional Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HardwareEngine")

@dataclass
class SystemSpecs:
    os_name: str
    cpu_cores: int
    total_ram_gb: float
    gpu_name: Optional[str] = None
    vram_gb: float = 0.0
    architecture: str = ""

class HardwareEngine:
    """
    High-level hardware diagnostic engine for automated model optimization.
    """
    def __init__(self):
        self.specs = self._detect_specs()

    def _detect_specs(self) -> SystemSpecs:
        ram = psutil.virtual_memory().total / (1024**3)
        cores = psutil.cpu_count(logical=True)
        arch = platform.machine()
        os_name = platform.system()
        
        gpu_name, vram = self._detect_gpu()
        
        return SystemSpecs(
            os_name=os_name,
            cpu_cores=cores,
            total_ram_gb=round(ram, 2),
            gpu_name=gpu_name,
            vram_gb=round(vram, 2),
            architecture=arch
        )

    def _detect_gpu(self) -> tuple[Optional[str], float]:
        """Detects NVIDIA GPU details using GPUtil or system commands."""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].name, gpus[0].memoryTotal / 1024
        except Exception:
            # Fallback for systems where GPUtil might fail or non-NVIDIA GPUs
            pass
        
        # Additional detection logic for Mac/Linux could be added here
        return None, 0.0

    def get_recommended_model(self) -> str:
        """
        Intelligent mapping of hardware to optimized local LLMs.
        """
        if self.specs.vram_gb >= 12:
            return "deepseek-coder-v2"
        elif self.specs.vram_gb >= 6 or self.specs.total_ram_gb >= 16:
            return "llama3:8b"
        elif self.specs.total_ram_gb >= 8:
            return "mistral"
        else:
            return "phi3:mini"

    def display_report(self):
        from rich.table import Table
        from rich.console import Console
        
        console = Console()
        table = Table(title="[bold blue]Hardware Diagnostic Report[/bold blue]")
        table.add_column("Component", style="cyan")
        table.add_column("Specification", style="magenta")
        
        table.add_row("OS", self.specs.os_name)
        table.add_row("CPU Cores", str(self.specs.cpu_cores))
        table.add_row("System RAM", f"{self.specs.total_ram_gb} GB")
        table.add_row("GPU", self.specs.gpu_name or "N/A (CPU Mode)")
        table.add_row("VRAM", f"{self.specs.vram_gb} GB")
        table.add_row("Architecture", self.specs.architecture)
        
        console.print(table)
        console.print(f"\n[green]Recommended Local Model:[/green] [bold yellow]{self.get_recommended_model()}[/bold yellow]\n")

if __name__ == "__main__":
    engine = HardwareEngine()
    engine.display_report()
