import requests
import json
import logging
from typing import Generator

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Robust Ollama API client for model management and inference.
    """
    BASE_URL = "http://localhost:11434/api"

    def __init__(self):
        self.verify_service()

    def verify_service(self):
        try:
            response = requests.get(f"{self.BASE_URL}/tags", timeout=3)
            response.raise_for_status()
        except Exception:
            raise ConnectionError("Ollama service is not reachable. Is it running?")

    def get_installed_models(self) -> list:
        response = requests.get(f"{self.BASE_URL}/tags")
        return [m['name'] for m in response.json().get('models', [])]

    def pull_model(self, name: str) -> Generator[dict, None, None]:
        url = f"{self.BASE_URL}/pull"
        with requests.post(url, json={"name": name}, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    def chat(self, model: str, prompt: str, system: str = "") -> Generator[dict, None, None]:
        url = f"{self.BASE_URL}/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": True
        }
        with requests.post(url, json=payload, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    # Yielding full chunk to get stats at the end
                    yield {
                        "response": chunk.get("response", ""),
                        "done": chunk.get("done", False),
                        "prompt_tokens": chunk.get("prompt_eval_count", 0),
                        "response_tokens": chunk.get("eval_count", 0)
                    }
