import os
import shutil
import subprocess
import sys
import ast
import re
import time
import zipfile

# Configuration
VERSION = "1.10.0"
SPEC_FILE = "Thunderz Assistant.spec"
DIST_DIR = "dist"
BUILD_DIR = "build"
EXE_NAME = "Thunderz Assistant.exe"
ZIP_NAME = f"Thunderz_Assistant_v{VERSION}.zip"

def get_project_imports():
    """Scans modules and main.py for third-party imports."""
    all_imports = {
        'tkinter.scrolledtext', 
        'PIL.Image', 
        'PIL.ImageDraw', 
        'PIL.ImageTk', 
        'pynvml', 
        'psutil', 
        'yfinance'
    }
    root_dir = os.path.dirname(os.path.abspath(__file__))
    # Removed 'tkinter' from STDLIB to ensure it's scanned properly
    STDLIB = {'os', 'sys', 'time', 'json', 'datetime', 'threading', 'webbrowser', 'hashlib', 'random', 'math'}

    for root, _, files in os.walk(root_dir):
        if any(x in root for x in [DIST_DIR, BUILD_DIR, '.git', '.venv']): continue
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    name = alias.name.split('.')[0]
                                    if name not in STDLIB: all_imports.add(name)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    name = node.module.split('.')[0]
                                    if name not in STDLIB: all_imports.add(name)
                                    if 'tkinter' in node.module: all_imports.add(node.module)
                    except: continue
    return sorted(list(all_imports))

def update_spec_file(imports):
    """Injects the found imports into the .spec file."""
    print(f"💉 Injecting hiddenimports: {imports}")
    with open(SPEC_FILE, 'r') as f:
        content = f.read()
    
    pattern = r"hiddenimports=\[.*?\]"
    replacement = f"hiddenimports={imports}"
    new_content = re.sub(pattern, replacement, content)
    
    with open(SPEC_FILE, 'w') as f:
        f.write(new_content)

def verify_and_bundle():
    """Checks build, copies notes, and creates a ZIP archive."""
    print("\n📦 Step 3: Verifying & Bundling...")
    exe_path = os.path.join(DIST_DIR, EXE_NAME)
    notes_src = os.path.join("docs", "versions", f"v{VERSION}_RELEASE_NOTES.md")
    notes_dest = os.path.join(DIST_DIR, f"v{VERSION}_RELEASE_NOTES.txt")

    if os.path.exists(exe_path):
        # 1. Copy Release Notes
        if os.path.exists(notes_src):
            shutil.copy2(notes_src, notes_dest)
            print(f"   ✅ Release notes added to {DIST_DIR}/")
        
        # 2. Create ZIP
        zip_path = os.path.join(os.getcwd(), ZIP_NAME)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(exe_path, EXE_NAME)
            if os.path.exists(notes_dest):
                zipf.write(notes_dest, os.path.basename(notes_dest))
        
        print(f"   ✅ SUCCESS! Bundle created: {ZIP_NAME}")
        print(f"   📍 Path: {zip_path}")
    else:
        print(f"   ❌ ERROR: {EXE_NAME} was not found!")

def clean_and_build():
    print("🧹 Step 1: Cleaning old builds...")
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            # Added a retry loop to handle locked files
            for i in range(3):
                try:
                    shutil.rmtree(d)
                    print(f"   ✅ Cleaned {d}/")
                    break
                except Exception as e:
                    if i < 2:
                        print(f"   ⚠️ {d}/ is locked, retrying in 2s...")
                        time.sleep(2)
                    else:
                        print(f"   ❌ Error: Could not clean {d}. Close any open folders/apps and try again.")
                        return

    imports = get_project_imports()
    update_spec_file(imports)
    
    print("\n🚀 Step 2: Starting PyInstaller Build...")
    try:
        subprocess.check_call([sys.executable, "-m", "PyInstaller", SPEC_FILE])
        verify_and_bundle()
    except subprocess.CalledProcessError as e:
        print(f"   ❌ PyInstaller failed: {e}")

if __name__ == "__main__":
    clean_and_build()