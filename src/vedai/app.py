"""
VedAI Native Desktop App — Main Entry Point

Runs FastAPI in a background thread, then opens a native
PyWebView window. No browser required!
"""

import threading
import time
import sys
import os
import webview
import uvicorn

# Resolve paths correctly whether running as .py or frozen .exe
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PORT = 8080


class VedAIApi:
    """
    PyWebView JavaScript API Bridge.
    Methods here are callable from JavaScript as:
        window.pywebview.api.method_name()
    """

    def choose_folder(self):
        """Open native OS folder picker dialog and return selected path."""
        result = webview.windows[0].create_file_dialog(
            webview.FOLDER_DIALOG
        )
        if result and len(result) > 0:
            return result[0]
        return None

    def get_app_path(self):
        """Return the base directory of the app."""
        return BASE_DIR


def start_server():
    """Run FastAPI server in background thread."""
    # Import here to avoid circular issues in frozen exe
    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
    sys.path.insert(0, BASE_DIR)

    from backend.main import app
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


def wait_for_server(timeout=15):
    """Wait until FastAPI is ready."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/status", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def launch():
    """Main launcher — start server thread then open native window."""

    # Start FastAPI in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    print("🔄 Starting VedAI backend...")
    if not wait_for_server():
        print("❌ Backend failed to start!")
        sys.exit(1)

    print("✅ Backend ready. Opening VedAI window...")

    # Create the native window
    api = VedAIApi()
    window = webview.create_window(
        title="VedAI Studio",
        url=f"http://127.0.0.1:{PORT}/",
        js_api=api,
        width=1280,
        height=800,
        min_size=(900, 600),
        background_color="#070b12",
        text_select=True,
        confirm_close=False
    )

    # Start PyWebView (this blocks until window is closed)
    webview.start(debug=False)


if __name__ == "__main__":
    launch()
