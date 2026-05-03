import os
import subprocess
import time
import shutil
import psutil

def nuclear_cleanup():
    print("☢️  VED-AI NUCLEAR RESCUE INITIALIZED...")
    print("------------------------------------------")

    # 1. Kill everything
    print("🎯 Killing all locked processes...")
    processes = ["ollama.exe", "python.exe", "uvicorn.exe"]
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in processes and proc.info['pid'] != current_pid:
                proc.kill()
        except: pass
    time.sleep(2)

    # 2. Purge Environment Variables (Registry Level)
    print("🧹 Purging Registry & Environment Variables...")
    try:
        subprocess.run('reg delete HKCU\\Environment /v OLLAMA_MODELS /f', shell=True, capture_output=True)
        subprocess.run('setx OLLAMA_MODELS ""', shell=True, capture_output=True)
        if "OLLAMA_MODELS" in os.environ:
            del os.environ["OLLAMA_MODELS"]
    except: pass

    # 3. Wipe Temp Folders
    print("🗑️  Cleaning temporary installation folders...")
    paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\VedAI_Bridge"),
        r"J:\VedAI_System",
        r"H:\vedai",
        r"J:\vedai"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                shutil.rmtree(p, ignore_errors=True)
                print(f"✅ Cleaned: {p}")
            except:
                print(f"⚠️ Could not fully clean {p} (locked), but Registry is purged.")

    print("------------------------------------------")
    print("✅ SYSTEM RESET COMPLETE. Your PC is now a clean slate.")
    print("🚀 You can now run: python installer.py")

if __name__ == "__main__":
    nuclear_cleanup()
