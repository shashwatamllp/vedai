from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
import json
import uvicorn
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="VedAI Web Studio API")

@app.get("/", response_class=HTMLResponse)
async def get_studio():
    studio_path = os.path.join(os.path.dirname(__file__), "ui", "studio.html")
    with open(studio_path, "r", encoding="utf-8") as f:
        return f.read()

from vedai.engine.ollama import OllamaClient
from vedai.engine.hardware import HardwareEngine
from vedai.engine.context import ContextManager
from vedai.engine.agent import AgentLoop
from vedai.engine.tools import ToolEngine

# Enable CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Instances
client = OllamaClient()
hw = HardwareEngine()
tools = ToolEngine()
ctx_mgr = ContextManager()

class ChatRequest(BaseModel):
    message: str
    model: str = "qwen2.5-coder:1.5b"

@app.get("/status")
async def get_status():
    return {
        "status": "ready",
        "hardware": hw.specs,
        "recommended_model": hw.get_recommended_model()
    }

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    agent = AgentLoop(client, tools, req.model)
    
    # Auto-index project
    files = ctx_mgr.scan()
    ctx_mgr.graph.index_project(files)
    
    # Build System Prompt (Truncated for speed)
    project_context = ctx_mgr.build_context()
    system_prompt = (
        "You are VedAI Web Studio. Provide expert coding help.\n"
        f"Context: {str(project_context)[:4000]}"
    )

    async def event_generator():
        for chunk in agent.run(req.message, system_prompt):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
