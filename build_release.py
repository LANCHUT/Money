import os
import shutil
import hashlib
import zipfile
import subprocess
import sys

PROJECT_NAME = "Money"
MAIN_SCRIPT = "Main.py"
ICON_PATH = "Finao.ico"
DIST_DIR = "dist"
BUILD_DIR = "build"
RELEASE_DIR = "release"

try:
    import PyInstaller
except ImportError:
    print("PyInstaller non trouvé dans ce Python. Installation en cours...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

for folder in [DIST_DIR, BUILD_DIR]:
    if os.path.exists(folder):
        shutil.rmtree(folder)

if not os.path.exists(RELEASE_DIR):
    os.makedirs(RELEASE_DIR)

print("Packaging avec PyInstaller...")
subprocess.run([
    sys.executable, "-m", "PyInstaller",
    "--clean",
    "--onefile",
    "--windowed",
    f"--icon={ICON_PATH}",
    MAIN_SCRIPT
], check=True)
