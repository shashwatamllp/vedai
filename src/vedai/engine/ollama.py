import httpx
import json
import logging
import asyncio
from typing import AsyncGenerator, Generator

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Robust Async Ollama API client for model management and inference.
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
        """Synchronous pull for installer/server recovery."""
        url = f"{self.base_url}/api/pull"
        import requests
        with requests.post(url, json={"name": name}, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    async def chat_async(self, model: str, messages: list) -> AsyncGenerator[dict, None]:
        """True async streaming chat using httpx."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code == 404:
                    yield {"message": {"content": f"❌ Model '{model}' not found. Please wait while I pull it."}}
                    return
                elif response.status_code != 200:
                    yield {"message": {"content": f"⚠️ Ollama Error ({response.status_code}). Please check your connection."}}
                    return

                async for line in response.aiter_lines():
                    if line:
                        yield json.loads(line)

    def chat(self, model: str, messages: list):
        """Legacy wrapper if needed, but chat_async is preferred."""
        # This is a bit of a hack to bridge sync/async if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return self.chat_async(model, messages)
