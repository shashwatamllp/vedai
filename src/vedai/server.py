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

# [USER OVERRIDE] Force J: Drive Environment if it exists
if os.path.exists("J:\\"):
    os.environ["OLLAMA_MODELS"] = r"J:\VedAI_System\Models"
    print(f"📍 Server strictly using J: Drive models: {os.environ['OLLAMA_MODELS']}")

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
    
    # Build System Prompt
    project_context = ctx_mgr.build_context()
    system_prompt = (
        "You are VedAI Web Studio. Provide expert coding help.\n"
        f"Context: {str(project_context)[:4000]}"
    )

    # [AUTONOMOUS RECOVERY] Check if model exists, if not pull it
    installed = client.get_installed_models()
    if req.model not in installed and (req.model + ":latest") not in installed:
        async def pull_and_stream():
            yield f"data: {json.dumps({'text': '📥 Model missing. Starting Autonomous Pull...'})}\n\n"
            try:
                for progress in client.pull_model(req.model):
                    status = progress.get('status', 'Downloading...')
                    yield f"data: {json.dumps({'text': f' [dim]Status: {status}[/dim]\n'})}\n\n"
                yield f"data: {json.dumps({'text': '✅ Pull Complete! Thinking...'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'text': f'❌ Pull Failed: {str(e)}'})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # Now run the actual chat
            for chunk in agent.run(req.message, system_prompt):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(pull_and_stream(), media_type="text/event-stream")

    async def event_generator():
        for chunk in agent.run(req.message, system_prompt):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
