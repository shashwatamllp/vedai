import os
import psutil
import shutil
import subprocess
import sys
from pathlib import Path

# Add src to path so we can use VSCodeManager
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
try:
    from vedai.engine.vscode_manager import VSCodeManager
except ImportError:
    VSCodeManager = None

def print_privacy_msg():
    print("\n" + "="*50)
    print("🔒 PRIVACY GUARANTEE: VedAI is 100% Local.")
    print("Your code and data NEVER leave your machine.")
    print("We do not collect any logs or information.")
    print("="*50 + "\n")

def check_ollama():
    print("🔍 Checking for Ollama...")
    try:
        # Check if ollama command exists
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        print("✅ Ollama is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama not found! VedAI requires Ollama for local AI.")
        print("🔗 Please download it from: https://ollama.com/download")
        return False

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

print_privacy_msg()
if not check_ollama():
    sys.exit(1)

best_drive = get_best_drive()
print(f"🚀 Best Drive Found for Models: {best_drive} ({psutil.disk_usage(best_drive).free // (1024**3)} GB Free)")

# Setup Smart Path
base_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base_dir, "logopic.png")

print("📦 Installing Python dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], shell=True)

if VSCodeManager:
    print("🔌 Integrating with VS Code...")
    vsc = VSCodeManager()
    result = vsc.configure_continue()
    print(result)

print("🎨 Creating Desktop Shortcut...")
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
shortcut_path = os.path.join(desktop, "VedAI Prime.lnk")

# PowerShell script to create shortcut with logo
ps_script = f"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut("{shortcut_path}")
$s.TargetPath = "{sys.executable}"
$s.Arguments = "-m vedai.cli chat"
$s.WorkingDirectory = "{base_dir}"
$s.IconLocation = "{logo_path}"
$s.Save()
"""
subprocess.run(["powershell", "-Command", ps_script], capture_output=True)

print("\n✨ INSTALLATION COMPLETE! VedAI is now your Local Coding Bridge.")
print("👉 Click the 'VedAI Prime' icon on your Desktop to start.")
