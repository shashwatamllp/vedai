import httpx
import requests


class OllamaClient:

    def __init__(self):

        self.base_url = (
            "http://localhost:11434"
        )

        self.model = (
            "llama3.2:latest"
        )

    def get_installed_models(self) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return [m['name'] for m in response.json().get('models', [])]
        except:
            return [self.model]

    async def generate(
        self,
        prompt: str
    ):

        async with httpx.AsyncClient(
            timeout=180
        ) as client:

            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )

            if response.status_code != 200:
                return f"Error from LLM: {response.text}"

            data = response.json()

            return data.get("response", str(data))
