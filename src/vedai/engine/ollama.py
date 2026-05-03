import httpx
import json
import logging
from typing import Generator

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Robust Ollama API client for model management and inference.
    """
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def get_installed_models(self) -> list:
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return [m['name'] for m in response.json().get('models', [])]
        except:
            return []

    def pull_model(self, name: str) -> Generator[dict, None, None]:
        url = f"{self.base_url}/api/pull"
        with httpx.stream("POST", url, json={"name": name}, timeout=None) as response:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    def chat(self, model: str, messages: list) -> Generator[dict, None, None]:
        """Streaming chat using httpx for async-friendly output."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        with httpx.stream("POST", url, json=payload, timeout=None) as response:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)
