import os
import psutil
import shutil
import subprocess
import sys
import time
import requests
from pathlib import Path

# Add src to path for VSCodeManager
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
try:
    from vedai.engine.vscode_manager import VSCodeManager
    from vedai.engine.hardware import HardwareEngine
except ImportError:
    VSCodeManager = None
    HardwareEngine = None

def print_banner():
    print("\n" + "="*60)
    print("🌌  VED-AI: THE AUTONOMOUS LOCAL CODING BRIDGE")
    print("Developed by Shashwatam Eco-Chie Creations LLP")
    print("="*60 + "\n")

def perform_deep_cleanup():
    print("🧹 [STAGE 1] Performing Deep System Cleanup...")
    targets = ["vedai", "vedai_apps", "VedAI_System", "vedai_venv"]
    for part in psutil.disk_partitions():
        if 'fixed' in part.opts:
            drive = part.mountpoint
            for target in targets:
                path = os.path.join(drive, target)
                if os.path.exists(path):
                    try:
                        print(f"🗑️ Removing old installation: {path}")
                        shutil.rmtree(path, ignore_errors=True)
                    except: pass
    print("✅ System is now a Clean Slate.")

def get_best_drive():
    best_drive = "C:\\"
    max_free = 0
    for part in psutil.disk_partitions():
        if 'fixed' in part.opts:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                if usage.free > max_free:
                    max_free = usage.free
                    best_drive = part.mountpoint
            except: pass
    return best_drive

def setup_ollama(download_path):
    print("🔍 [STAGE 2] Checking for Ollama Engine...")
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        print("✅ Ollama is already installed.")
    except:
        print("❌ Ollama not found. Starting Autonomous Download...")
        url = "https://ollama.com/download/OllamaSetup.exe"
        setup_file = os.path.abspath(os.path.join(download_path, "OllamaSetup.exe"))
        
        try:
            print(f"📥 Downloading to: {setup_file}")
            
            # Step A: Progress hook for urllib
            def progress_hook(count, block_size, total_size):
                if total_size > 0:
                    downloaded = count * block_size
                    done = int(50 * downloaded / total_size)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded//(1024*1024)}MB/{total_size//(1024*1024)}MB")
                    sys.stdout.flush()

            # Step B: Use urllib for low-level reliable download
            import urllib.request
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            
            urllib.request.urlretrieve(url, setup_file, reporthook=progress_hook)
            
            print(f"\n📥 Download Complete. size: {os.path.getsize(setup_file) // 1024**2} MB")
            
            # Step C: Execute
            print("🚀 Launching Ollama installer...")
            # Use os.system as the absolute most basic way to trigger an exe on Windows
            exit_code = os.system(f'"{setup_file}" /silent')
            if exit_code != 0:
                print(f"⚠️ Installer exited with code {exit_code}, trying direct launch...")
                subprocess.run([setup_file, "/silent"], check=True)
            
            print("✅ Ollama installed successfully.")
            time.sleep(5)
        except Exception as e:
            print(f"\n❌ Error during Ollama setup: {type(e).__name__} - {e}")
            return False
    return True

def main():
    print_banner()
    
    # 1. Cleanup
    perform_deep_cleanup()
    
    # 2. Drive Selection
    best_drive = get_best_drive()
    install_path = os.path.join(best_drive, "VedAI_System")
    os.makedirs(install_path, exist_ok=True)
    print(f"🚀 Installation Target: {install_path} ({psutil.disk_usage(best_drive).free // (1024**3)} GB Free)")

    # 3. Ollama Setup
    if not setup_ollama(install_path):
        sys.exit(1)

    # 4. App & Environment Setup
    print("📦 [STAGE 3] Building Private Environment & Dependencies...")
    venv_path = os.path.join(install_path, "venv")
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    
    pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    
    # Install with no-cache to avoid disk issues
    subprocess.run([pip_exe, "install", "--no-cache-dir", "-e", "."], check=True)
    print("✅ Environment Ready.")

    # 5. Model Selection & Pre-pull
    if HardwareEngine:
        hw = HardwareEngine()
        model = hw.get_recommended_model()
        print(f"🤖 [STAGE 4] Hardware detected. Recommended Model: {model}")
        print(f"📥 Pulling {model} in background (this may take a few minutes)...")
        # Set OLLAMA_MODELS to our smart drive
        os.environ["OLLAMA_MODELS"] = os.path.join(install_path, "Models")
        os.makedirs(os.environ["OLLAMA_MODELS"], exist_ok=True)
        subprocess.Popen(["ollama", "pull", model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 6. VS Code Integration
    if VSCodeManager:
        print("🔌 [STAGE 5] Integrating with VS Code...")
        vsc = VSCodeManager()
        print(vsc.configure_continue())

    # 7. Desktop Shortcut
    print("🎨 [STAGE 6] Creating Premium Desktop Shortcut...")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "VedAI Prime.lnk")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "logopic.png")

    ps_script = f"""
    $s = (New-Object -ComObject WScript.Shell).CreateShortcut("{shortcut_path}")
    $s.TargetPath = "{python_exe}"
    $s.Arguments = "-m vedai.cli chat"
    $s.WorkingDirectory = "{base_dir}"
    $s.IconLocation = "{logo_path}"
    $s.Save()
    """
    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)

    print("\n" + "="*60)
    print("✨ SUCCESS: VedAI is now fully operational!")
    print(f"📍 Location: {install_path}")
    print("👉 Click 'VedAI Prime' on your Desktop to start coding.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
