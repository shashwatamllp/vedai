import os
import psutil
import shutil
import subprocess
from pathlib import Path

def print_privacy_msg():
    print("\n" + "="*50)
    print("🔒 PRIVACY GUARANTEE: VedAI is 100% Local.")
    print("Your code and data NEVER leave your machine.")
    print("We do not collect any logs or information.")
    print("="*50 + "\n")

def cleanup_old_installs(current_drive):
    print("🧹 Scanning for old installations to save space...")
    for part in psutil.disk_partitions():
        drive = part.mountpoint
        if drive != current_drive and os.path.exists(os.path.join(drive, "vedai")):
            try:
                shutil.rmtree(os.path.join(drive, "vedai"))
                print(f"✅ Removed old installation from {drive}")
            except: pass

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
best_drive = get_best_drive()
print(f"🚀 Best Drive Found: {best_drive} ({psutil.disk_usage(best_drive).free // (1024**3)} GB Free)")

# Setup Smart Path
install_path = os.path.join(best_drive, "vedai_apps")
os.makedirs(install_path, exist_ok=True)
os.environ['TEMP'] = os.path.join(install_path, "tmp")
os.makedirs(os.environ['TEMP'], exist_ok=True)

cleanup_old_installs(best_drive)

print("📦 Installing dependencies...")
subprocess.run(["pip", "install", "-e", "."], shell=True)

print("🎨 Creating Desktop Shortcut with Logo...")
# PowerShell script to create shortcut with logo
ps_script = f"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut("$home\\Desktop\\VedAI Prime.lnk")
$s.TargetPath = "python.exe"
$s.Arguments = "-m src.vedai.cli chat"
$s.IconLocation = "H:\\ved4you\\logopic.png"
$s.Save()
"""
subprocess.run(["powershell", "-Command", ps_script], capture_output=True)

print("\n✨ INSTALLATION COMPLETE! Check your Desktop for VedAI Prime.")
