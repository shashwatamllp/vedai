import os
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class VSCodeManager:
    """
    Automates VS Code configuration for local AI integration.
    Installs and configures Cline (OpenClaw clone) and Continue.
    """
    def __init__(self):
        self.continue_config_path = Path(os.path.expanduser("~/.continue/config.json"))
        # Windows APPDATA path for Cline
        appdata = os.environ.get("APPDATA", "")
        self.cline_config_path = Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_api_settings.json"

    def install_extensions(self):
        print("📦 Installing VS Code AI Extensions (Cline & Continue)...")
        try:
            subprocess.run(["code", "--install-extension", "saoudrizwan.claude-dev"], check=True, capture_output=True)
            subprocess.run(["code", "--install-extension", "Continue.continue"], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.warning(f"Failed to install extensions via CLI: {e}")
            return False

    def configure_continue(self, model_name: str):
        self.continue_config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if self.continue_config_path.exists():
                with open(self.continue_config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {"models": [], "tabAutocompleteModel": {}}

            local_model = {
                "title": f"VedAI ({model_name})",
                "provider": "ollama",
                "model": model_name
            }

            # Remove old VedAI entries
            config["models"] = [m for m in config.get("models", []) if not str(m.get("title", "")).startswith("VedAI")]
            config["models"].insert(0, local_model)
            config["tabAutocompleteModel"] = local_model
            
            with open(self.continue_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Continue Config Error: {e}")
            return False

    def configure_cline(self, model_name: str):
        self.cline_config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            config = {
                "apiProvider": "ollama",
                "apiModelId": model_name,
                "ollamaModelId": model_name,
                "ollamaBaseUrl": "http://localhost:11434"
            }
            with open(self.cline_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Cline Config Error: {e}")
            return False

    def setup_all(self, model_name: str) -> str:
        self.install_extensions()
        continue_ok = self.configure_continue(model_name)
        cline_ok = self.configure_cline(model_name)
        
        if continue_ok and cline_ok:
            return f"✅ VS Code is now configured as an Autonomous Agent using '{model_name}'!"
        return "⚠️ VS Code configuration partially failed. You may need to set the model manually."
