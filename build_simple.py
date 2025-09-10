import subprocess
import sys
import os

def build_simple():
    """Build with minimal options"""
    print("🚀 Building simple version...")
    
    # Check if main file exists
    if not os.path.exists("tubeRocket_gui.py"):
        print("❌ tubeRocket_gui.py not found!")
        return False
    
    # Simple command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name=TubeRocket-Simple",
        "tubeRocket_gui.py"
    ]
    
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        print("✅ Simple build successful!")
        return True
    except Exception as e:
        print(f"❌ Simple build failed: {e}")
        return False

if __name__ == "__main__":
    build_simple()
