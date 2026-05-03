import psutil
import platform
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

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
    Advanced hardware diagnostic engine for automated model optimization.
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

    def _detect_gpu(self) -> Tuple[Optional[str], float]:
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].name, gpus[0].memoryTotal / 1024
        except Exception as e:
            logger.debug(f"GPU detection failed: {e}")
        return None, 0.0

    def get_recommended_model(self) -> str:
        if self.specs.vram_gb >= 12:
            return "deepseek-coder-v2"
        elif self.specs.vram_gb >= 6 or self.specs.total_ram_gb >= 16:
            return "llama3:8b"
        elif self.specs.total_ram_gb >= 8:
            return "mistral"
        else:
            return "phi3:mini"
