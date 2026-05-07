import os
import json
import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from backend.agents.runtime import RuntimeAgent
from backend.core.ollama import OllamaClient

app = FastAPI(title="VedAI Runtime", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

runtime = RuntimeAgent()
client = OllamaClient()


@app.get("/", response_class=HTMLResponse)
async def get_studio():
    studio_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "vedai", "ui", "studio.html"
    )
    try:
        with open(studio_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>UI not found. Ensure src/vedai/ui/studio.html exists.</h1>"


@app.get("/status")
async def get_status():
    cpu_cores = psutil.cpu_count(logical=True)
    ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    installed_models = client.get_installed_models()
    recommended = installed_models[0] if installed_models else client.model

    return {
        "status": "ready",
        "hardware": {
            "cpu_cores": cpu_cores,
            "ram_gb": ram_gb
        },
        "recommended_model": recommended,
        "installed_models": installed_models
    }


class ChatPayload(BaseModel):
    message: str
    model: str = "llama3.2:latest"


@app.post("/chat")
async def chat(payload: ChatPayload):
    # Set model from UI selection
    runtime.planner.llm.model = payload.model
    runtime.corrector.llm.model = payload.model

    async def event_stream():
        def send(text: str):
            return f"data: {json.dumps({'text': text})}\n\n"

        yield send("🧠 **[Step 1] Planning your task...**\n")

        result = await runtime.run(payload.message)

        plan = result.get("plan", "")
        yield send(f"\n📋 **Plan:**\n{plan}\n\n")

        exec_result = result.get("execution", {})
        actions_taken = exec_result.get("actions_taken", [])

        if actions_taken:
            yield send("⚙️ **[Step 2] Executing...**\n")
            for action in actions_taken:
                status = action.get("status", "")
                action_name = action.get("action", "")
                yield send(f"  {status} `{action_name}`\n")
                if action.get("stdout"):
                    yield send(f"  ```\n{action['stdout'].strip()}\n  ```\n")
                if action.get("error"):
                    yield send(f"  ⚠️ Error: {action['error']}\n")

        verification = result.get("verification", {})
        attempts = result.get("attempts", 1)

        if result.get("status") == "success":
            yield send(f"\n{verification.get('summary', '✅ Done!')}\n")
            if attempts > 1:
                yield send(f"🔄 Self-corrected in {attempts} attempt(s).\n")
        else:
            yield send(f"\n{verification.get('summary', '❌ Failed')}\n")
            errors = result.get("errors", [])
            for err in errors:
                yield send(f"  ❌ {err}\n")
            yield send("💡 Please refine your request or check the error above.\n")

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
