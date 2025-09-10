import subprocess
import sys
import os

def build_debug():
    """Build debug version with console"""
    print("🐛 Building debug version with console...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",  # Show console
        "--name=TubeRocket-Debug",
        "--clean",
        "tubeRocket_gui.py"
    ]
    
    try:
        print(f"Command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print("✅ Debug build successful!")
        print("📁 Location: dist/TubeRocket-Debug.exe")
        print("🐛 This version shows console for debugging")
        return True
    except Exception as e:
        print(f"❌ Debug build failed: {e}")
        return False

if __name__ == "__main__":
    build_debug()
