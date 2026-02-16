# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # (Source Path, Destination Path inside EXE)
        ('modules', 'modules'),
        ('data.example', 'data.example'),
        ('media', 'media'),
        ('thunderz_icon.ico', '.'),
        ('docs', 'docs')
    ],
    # Hidden imports are libraries that PyInstaller sometimes misses
    hiddenimports=['PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageTk', 'ast', 'asyncio', 'av', 'bs4', 'config', 'csv', 'ctypes', 'cv2', 'dashboard_module', 'diffusers', 'discord_integration_module', 'discord_presence_module', 'discord_webhook_module', 'file_organizer_module', 'glizzy_module', 'html', 'imageio', 'importlib', 'inspect', 'io', 'logging', 'matplotlib', 'news_module', 'notes_module', 'notification_center_module', 'notification_manager', 'pathlib', 'pomodoro_module', 'psutil', 'pygame', 'pynvml', 'pypresence', 'pystray', 're', 'requests', 'shutil', 'stock_monitor_module', 'subprocess', 'system_monitor_module', 'tempfile', 'tkinter', 'tkinter.scrolledtext', 'torch', 'traceback', 'tray_manager', 'typing', 'uuid', 'weather_module', 'win32gui', 'win32process', 'winsdk', 'winsound', 'yfinance', 'yt_dlp', 'zipfile'],    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Thunderz Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements=None,
    icon='thunderz_icon.ico',
)