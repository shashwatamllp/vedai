import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from backend.agents.runtime import RuntimeAgent
from backend.core.ollama import OllamaClient

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

# Added Client for the /status endpoint
client = OllamaClient()

@app.get("/", response_class=HTMLResponse)
async def get_studio():
    # Load the UI from the original src directory
    studio_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "vedai", "ui", "studio.html")
    try:
        with open(studio_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "UI file not found. Ensure src/vedai/ui/studio.html exists."

@app.get("/status")
async def get_status():
    import psutil
    cpu_cores = psutil.cpu_count(logical=True)
    ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    
    return {
        "status": "ready",
        "hardware": {
            "cpu_cores": cpu_cores,
            "ram_gb": ram_gb,
            "has_gpu": False # Placeholder
        },
        "recommended_model": client.model,
        "installed_models": [client.model]
    }

class ChatPayload(BaseModel):
    message: str   # UI sends "message"
    model: str = "qwen2.5-coder:1.5b" # UI sends "model"

@app.post("/chat")
async def chat(payload: ChatPayload):
    # The UI expects an SSE stream.
    async def event_generator():
        yield f"data: {json.dumps({'text': '🤔 Thinking (Planner)...'})}\n\n"
        
        result = await runtime.run(payload.message)
        
        # Send the final plan and result
        plan = result.get("plan", "")
        yield f"data: {json.dumps({'text': f'\n**Plan:**\n{plan}\n'})}\n\n"
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
