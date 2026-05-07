# VedAI Native App - PyInstaller Build Spec
# Run: pyinstaller vedai.spec

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files
datas = [
    ('src/vedai/ui', 'vedai/ui'),           # HTML UI files
    ('backend', 'backend'),                   # Backend agents
    ('src/vedai', 'vedai'),                   # Source
]

# Collect hidden imports
hidden_imports = [
    'uvicorn.logging',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'fastapi',
    'starlette',
    'httpx',
    'psutil',
    'webview',
    'backend.main',
    'backend.agents.runtime',
    'backend.agents.planner',
    'backend.agents.executor',
    'backend.agents.verifier',
    'backend.agents.self_corrector',
    'backend.core.ollama',
    'backend.core.state',
    'backend.memory.project_memory',
    'backend.memory.context_memory',
]

a = Analysis(
    ['src/vedai/app.py'],
    pathex=['.', 'src'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VedAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No black console window!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/vedai.ico',    # App icon
)
