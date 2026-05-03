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
        """Streaming chat using httpx with robust error handling."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        try:
            with httpx.stream("POST", url, json=payload, timeout=None) as response:
                if response.status_code == 404:
                    yield {"message": {"content": f"❌ Model '{model}' not found. Please wait while I pull it or run 'ollama pull {model}' in terminal."}}
                    return
                elif response.status_code != 200:
                    yield {"message": {"content": f"⚠️ Ollama Error ({response.status_code}). Check if your storage drive is connected."}}
                    return
                
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        yield chunk
        except Exception as e:
            # Check for disk/device errors
            if "device" in str(e).lower() or "exist" in str(e).lower():
                yield {"message": {"content": "❌ Critical Storage Error: J: drive disconnected. Re-run installer to fix."}}
            else:
                yield {"message": {"content": f"❌ Connection Error: {str(e)}"}}
