import os
import json
import psutil
from pathlib import Path
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

# Default workspace = current directory
_current_workspace = str(Path(".").resolve())
runtime = RuntimeAgent(workspace=_current_workspace)
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
        "hardware": {"cpu_cores": cpu_cores, "ram_gb": ram_gb},
        "recommended_model": recommended,
        "installed_models": installed_models,
        "workspace": _current_workspace
    }


@app.get("/browse")
async def browse_filesystem(path: str = ""):
    """Browse the local filesystem for project folder selection."""
    import string

    if not path:
        # Return available drives on Windows
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    usage = psutil.disk_usage(drive)
                    drives.append({
                        "name": drive,
                        "path": drive,
                        "type": "drive",
                        "free_gb": round(usage.free / (1024**3), 1)
                    })
                except: pass
        return {"current": "", "parent": None, "items": drives}

    # List directory contents
    target = Path(path)
    if not target.exists() or not target.is_dir():
        return {"error": "Path not found", "current": path, "items": []}

    items = []
    try:
        for item in sorted(target.iterdir()):
            if item.name.startswith('.') or item.name in ('$Recycle.Bin', 'System Volume Information'):
                continue
            if item.is_dir():
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "dir"
                })
    except PermissionError:
        pass

    parent = str(target.parent) if target.parent != target else None
    return {
        "current": str(target),
        "parent": parent,
        "items": items
    }


class WorkspacePayload(BaseModel):
    path: str


@app.post("/connect")
async def connect_project(payload: WorkspacePayload):
    """Connect to a project folder — creates VedAI.md and reinitializes the agent."""
    global runtime, _current_workspace

    path = Path(payload.path)
    if not path.exists():
        return {"success": False, "error": f"Path does not exist: {payload.path}"}
    if not path.is_dir():
        return {"success": False, "error": f"Path is not a directory: {payload.path}"}

    _current_workspace = str(path.resolve())
    runtime = RuntimeAgent(workspace=_current_workspace)  # Reinitialize — this creates VedAI.md + VedAI-map.md

    memory_summary = runtime.project_memory.build_agent_context()
    vedai_md_path = str(path / "VedAI.md")
    vedai_map_path = str(path / "VedAI-map.md")

    return {
        "success": True,
        "workspace": _current_workspace,
        "vedai_md": vedai_md_path,
        "vedai_map": vedai_map_path,
        "memory_summary": memory_summary
    }


@app.get("/workspace/memory")
async def get_memory():
    """Return contents of VedAI.md and VedAI-map.md for the UI Memory tab."""
    return {
        "vedai_md": runtime.project_memory.read(),
        "vedai_map": runtime.project_memory.read_map()
    }


@app.get("/workspace/tree")
async def get_file_tree():
    """Return file tree of connected workspace for display in UI."""
    workspace = Path(_current_workspace)
    files = []
    try:
        for item in sorted(workspace.rglob("*")):
            # Skip hidden dirs, __pycache__, .git
            parts = item.parts
            if any(p.startswith('.') or p == '__pycache__' or p == 'node_modules' for p in parts):
                continue
            rel = item.relative_to(workspace)
            files.append({
                "path": str(rel).replace("\\", "/"),
                "is_dir": item.is_dir(),
                "depth": len(rel.parts) - 1
            })
    except Exception as e:
        return {"files": [], "error": str(e)}
    return {"files": files[:200], "workspace": _current_workspace}  # cap at 200 items


class ChatPayload(BaseModel):
    message: str
    model: str = "llama3.2:latest"


@app.post("/chat")
async def chat(payload: ChatPayload):
    runtime.planner.llm.model = payload.model
    runtime.corrector.llm.model = payload.model

    async def event_stream():
        def send(text: str):
            return f"data: {json.dumps({'text': text})}\n\n"

        yield send(f"📁 **Workspace:** `{_current_workspace}`\n")
        yield send("🧠 **[Step 1] Planning...**\n")

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
                    yield send(f"```\n{action['stdout'].strip()}\n```\n")
                if action.get("error"):
                    yield send(f"  ⚠️ Error: {action['error']}\n")

        verification = result.get("verification", {})
        attempts = result.get("attempts", 1)

        if result.get("status") == "success":
            yield send(f"\n{verification.get('summary', '✅ Done!')}\n")
            if attempts > 1:
                yield send(f"🔄 Self-corrected in {attempts} attempt(s).\n")
            yield send("📝 **Saved to VedAI.md**\n")
        else:
            yield send(f"\n{verification.get('summary', '❌ Failed')}\n")
            for err in result.get("errors", []):
                yield send(f"  ❌ {err}\n")
            yield send("💡 Please refine your request or check the error above.\n")

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
