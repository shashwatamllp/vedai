import httpx


class OllamaClient:

    def __init__(self):

        self.base_url = (
            "http://localhost:11434"
        )

        self.model = (
            "qwen2.5-coder:7b"
        )

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
