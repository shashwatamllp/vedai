from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agents.runtime import RuntimeAgent

app = FastAPI(
    title="VedAI Runtime",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

runtime = RuntimeAgent()


class ChatPayload(BaseModel):
    prompt: str


@app.post("/chat")
async def chat(payload: ChatPayload):

    result = await runtime.run(
        payload.prompt
    )

    return result
