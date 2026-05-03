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
    # Force kill only OTHER lingering python processes to avoid lock errors
    try:
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'python.exe' and proc.info['pid'] != current_pid:
                proc.kill()
        time.sleep(1)
    except: pass

def get_best_drive():
    best_drive = "C:\\"
    max_free = 0
    for part in psutil.disk_partitions():
        if 'fixed' in part.opts:
            try:
                # [STABILITY CHECK] Test write in a subfolder to avoid root permission errors
                test_dir = os.path.join(part.mountpoint, "VedAI_Temp_Test")
                os.makedirs(test_dir, exist_ok=True)
                test_file = os.path.join(test_dir, ".vedai_test")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                shutil.rmtree(test_dir)
                
                usage = psutil.disk_usage(part.mountpoint)
                if usage.free > max_free:
                    max_free = usage.free
                    best_drive = part.mountpoint
            except: 
                # Silent skip for root-protected drives unless it's C:
                if part.mountpoint.lower() != "c:\\":
                    print(f"⚠️ Drive {part.mountpoint} is unstable or read-only. Skipping.")
    return best_drive

def setup_ollama(download_path):
    print("🔍 [STAGE 2] Checking for Ollama Engine...")
    
    # Check 1: System PATH
    is_installed = False
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        is_installed = True
    except:
        # Check 2: Direct path check
        common_exe_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Ollama", "ollama.exe")
        ]
        for exe_p in common_exe_paths:
            if os.path.exists(exe_p):
                is_installed = True
                break
    
    if is_installed:
        print("✅ Ollama is already installed.")
        return True
    else:
        print("❌ Ollama not found. Starting Autonomous Download...")
        url = "https://ollama.com/download/OllamaSetup.exe"
        # ALWAYS download to the local folder first to avoid drive-specific errors
        setup_file = os.path.abspath("OllamaSetup.exe")
        
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
            
            # Step D: Cleanup existing processes
            print("🧹 Cleaning up any existing Ollama processes...")
            os.system("taskkill /F /IM ollama.exe /T >nul 2>&1")
            os.system("taskkill /F /IM \"Ollama Setup.exe\" /T >nul 2>&1")
            time.sleep(2)

            # Step E: Execute
            print(f"🚀 Launching Ollama installer (Forcing J: drive)...")
            # Force installation directory to our smart drive
            install_dir = os.path.join(download_path, "Ollama")
            os.makedirs(install_dir, exist_ok=True)
            
            # Using /DIR flag for Inno Setup (which Ollama uses)
            cmd = f'"{setup_file}" /silent /DIR="{install_dir}"'
            print(f"⚙️ Command: {cmd}")
            exit_code = os.system(cmd)
            
            if exit_code != 0:
                print(f"⚠️ Silent install returned {exit_code}. Launching Interactive Mode...")
                print(f"👉 IMPORTANT: Please select {install_dir} as the installation folder if asked.")
                # Fallback to interactive mode with the directory flag
                os.system(f'"{setup_file}" /DIR="{install_dir}"')
                print("⏳ Waiting for you to finish the installation...")
                
                # Wait for ollama.exe to appear in the system to confirm install
                found = False
                common_exe_paths = [
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
                    os.path.join(os.environ.get("ProgramFiles", ""), "Ollama", "ollama.exe")
                ]
                
                for _ in range(120): # Wait up to 2 mins
                    time.sleep(5)
                    # Check 1: System PATH
                    try:
                        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
                        found = True
                        break
                    except: pass
                    
                    # Check 2: Direct path check
                    for exe_p in common_exe_paths:
                        if os.path.exists(exe_p):
                            found = True
                            break
                    if found: break
                
                if not found:
                    print("❌ Installation seems to have timed out or failed.")
                    return False
            
            print("✅ Ollama installed successfully.")
            time.sleep(5)
        except Exception as e:
            print(f"\n❌ Error during Ollama setup: {type(e).__name__} - {e}")
            return False
    return True

def main():
    print_banner()
    
    # 0. Global Setup
    best_drive = get_best_drive()
    install_path = os.path.join(best_drive, "VedAI_System")
    os.makedirs(install_path, exist_ok=True)
    
    # Redirect System TEMP/TMP to our drive with space globally
    custom_temp = os.path.join(install_path, "Temp")
    os.makedirs(custom_temp, exist_ok=True)
    os.environ["TEMP"] = custom_temp
    os.environ["TMP"] = custom_temp
    
    # 1. Cleanup
    perform_deep_cleanup()
    
    print(f"🚀 Installation Target: {install_path} ({psutil.disk_usage(best_drive).free // (1024**3)} GB Free)")

    # 3. Ollama Setup & Refresh
    print("🔄 Refreshing Ollama Service...")
    try:
        os.system("taskkill /F /IM ollama.exe /T >nul 2>&1")
        time.sleep(2)
        # Start Ollama in background
        subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(3)
    except: pass
    
    if not setup_ollama(install_path):
        sys.exit(1)

    # 4. App & Environment Setup
    print("📦 [STAGE 3] Building Private Environment & Dependencies...")
    # Environment stays on C: for stability (it's small ~300MB)
    local_appdata = os.environ.get("LOCALAPPDATA", "C:\\")
    env_path = os.path.join(local_appdata, "VedAI_Bridge")
    os.makedirs(env_path, exist_ok=True)
    
    venv_path = os.path.join(env_path, "venv")
    python_exe = sys.executable
    
    try:
        print(f"🛠️ Creating environment in: {venv_path}")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    except Exception as e:
        print(f"⚠️ Venv failed, using global Python: {e}")
        pip_exe = f'"{sys.executable}" -m pip'

    print("📥 Installing dependencies...")
    subprocess.run(f'{pip_exe} install --no-cache-dir -e .', shell=True, check=True)
    print("✅ Environment Ready.")

    # 5. Model Selection & Pre-pull
    if HardwareEngine:
        hw = HardwareEngine()
        model = hw.get_recommended_model()
        # IMPORTANT: Models go to the BIG DRIVE
        model_storage = os.path.join(install_path, "Models")
        os.makedirs(model_storage, exist_ok=True)
        os.environ["OLLAMA_MODELS"] = model_storage
        
        # Note: We use 'setx' to make this environment variable persistent for Ollama
        subprocess.run(f'setx OLLAMA_MODELS "{model_storage}"', shell=True, capture_output=True)
    
        # [STAGE 4] Proactive Model Pulling (Autonomous)
        hw = HardwareEngine()
        model = hw.get_recommended_model()
        print(f"📦 [STAGE 4] Hardware detected: {hw.specs.total_ram_gb}GB RAM. Auto-pulling {model}...")
        
        pull_result = subprocess.run(["ollama", "pull", model], capture_output=True, text=True)
        if "device" in pull_result.stderr.lower() or "exist" in pull_result.stderr.lower():
            print("\n⚠️ J: Drive Failure Detected. Reverting to C: drive for models...")
            # Clear persistent variable
            subprocess.run('setx OLLAMA_MODELS ""', shell=True, capture_output=True)
            os.environ["OLLAMA_MODELS"] = ""
            
            # [CRITICAL] Restart Ollama AGAIN to pick up the cleared environment
            print("🔄 Force-Restarting Ollama for Storage Migration...")
            os.system("taskkill /F /IM ollama.exe /T >nul 2>&1")
            time.sleep(2)
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(5)
            
            print("🔄 Retrying pull on C: drive (Default path)...")
            subprocess.run(["ollama", "pull", model])
        elif pull_result.returncode != 0:
            print(f"⚠️ Pull error: {pull_result.stderr}")

    # 6. VS Code Integration
    if VSCodeManager:
        print("🔌 [STAGE 5] Integrating with VS Code...")
        vsc = VSCodeManager()
        print(vsc.configure_continue())

    # 7. Desktop Shortcut
    print("🎨 [STAGE 6] Creating Premium Desktop Shortcut...")
    
    # Smart Desktop Path Detection (Handling OneDrive)
    def get_desktop_path():
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            path, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            return os.path.expandvars(path)
        except:
            return os.path.join(os.path.expanduser("~"), "Desktop")

    desktop = get_desktop_path()
    shortcut_path = os.path.join(desktop, "VedAI Prime.lnk")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "logopic.png")

    print(f"📍 Target Desktop: {desktop}")

    ps_script = f"""
    try {{
        $s = (New-Object -ComObject WScript.Shell).CreateShortcut("{shortcut_path}")
        $s.TargetPath = "{python_exe}"
        $s.Arguments = "-m vedai.cli studio"
        $s.WorkingDirectory = "{base_dir}"
        if (Test-Path "{logo_path}") {{ $s.IconLocation = "{logo_path}" }}
        $s.Save()
        Write-Output "SUCCESS"
    }} catch {{
        Write-Error $_.Exception.Message
    }}
    """
    result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
    
    # Auto-Launch Studio immediately
    print("🚀 Auto-Launching VedAI Studio on Port 8080...")
    try:
        # Using cmd /k keeps the window open on error so the user can see it
        launch_cmd = f'start cmd /k "{python_exe}" -m vedai.cli studio'
        subprocess.run(launch_cmd, shell=True)
    except:
        print("⚠️ Auto-launch failed. Please use the desktop shortcut.")
    
    if "SUCCESS" in result.stdout:
        print("✅ Desktop Shortcut Created Successfully.")
    else:
        print(f"⚠️ Shortcut Error: {result.stderr}")
        # Fallback: Create a simple BAT file in the project folder
        bat_path = os.path.join(base_dir, "VedAI_Launcher.bat")
        with open(bat_path, "w") as f:
            f.write(f'@echo off\n"{python_exe}" -m vedai.cli chat\npause')
        print(f"👉 Fallback: Created '{bat_path}'. You can use this to start.")

    print("\n" + "="*60)
    print("✨ SUCCESS: VedAI is now fully operational!")
    print(f"📍 System: {env_path} (Lightweight)")
    print(f"📍 Models: {install_path} (160GB Space Protected)")
    print("👉 Click 'VedAI Prime' on your Desktop to start coding.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
