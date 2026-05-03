import os
import json
import logging
from pathlib import Path

class VSCodeManager:
    """
    Automates VS Code configuration for local AI integration.
    Supports the 'Continue' extension.
    """
    def __init__(self):
        self.continue_config_path = Path(os.path.expanduser("~/.continue/config.json"))

    def configure_continue(self):
        if not self.continue_config_path.parent.exists():
            return "❌ Continue extension config folder not found. Please install the 'Continue' extension in VS Code first."

        try:
            if self.continue_config_path.exists():
                with open(self.continue_config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {"models": [], "tabAutocompleteModel": {}}

            # Add Ollama local model if not present
            local_model = {
                "title": "VedAI (Local)",
                "provider": "ollama",
                "model": "llama3"
            }

            if not any(m.get("title") == "VedAI (Local)" for m in config.get("models", [])):
                config.setdefault("models", []).append(local_model)
                config["tabAutocompleteModel"] = local_model
                
                with open(self.continue_config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                return "✅ VS Code 'Continue' extension configured to use VedAI (Local)!"
            else:
                return "ℹ️ VedAI is already configured in VS Code."
        except Exception as e:
            return f"❌ Error configuring VS Code: {str(e)}"
