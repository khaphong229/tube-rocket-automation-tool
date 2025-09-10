import subprocess
import sys
import os
import shutil
import glob

def clean_build():
    """Clean old build files"""
    print("🧹 Cleaning old build files...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"   Removed {dir_name}/")
            except Exception as e:
                print(f"   Warning: Could not remove {dir_name}: {e}")
    
    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"   Removed {file}")
            except Exception as e:
                print(f"   Warning: Could not remove {file}: {e}")

def check_pyinstaller():
    """Check if PyInstaller is accessible"""
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ PyInstaller version: {result.stdout.strip()}")
            return True
        else:
            print("❌ PyInstaller not working properly")
            return False
    except FileNotFoundError:
        print("❌ PyInstaller not found")
        return False
    except Exception as e:
        print(f"❌ Error checking PyInstaller: {e}")
        return False

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_build.txt"])
        return True
    except Exception as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def build_exe():
    """Build the executable"""
    print("🚀 Building TubeRocket.exe...")
    
    # Check current directory
    print(f"📂 Current directory: {os.getcwd()}")
    
    # All required files
    include_files = [
        "tubeRocket_gui.py",
        "account_dialog.py",
        "database.py", 
        "proxy_manager.py",
        "tuberocket_worker.py",
        "export_dialog.py",
        "import_dialog.py"
    ]
    
    # Check if all files exist
    print("📋 Checking required files...")
    missing_files = []
    for file in include_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing required files: {', '.join(missing_files)}")
        print("   Make sure all Python files are in the same directory as build.py")
        return False
    
    # Check PyInstaller
    if not check_pyinstaller():
        print("❌ PyInstaller check failed")
        return False
    
    # Data files to bundle
    data_files = []
    if os.path.exists("encryption.key"):
        data_files.append(("encryption.key", "."))
        print("   ✅ Found encryption.key")
    
    # Icon parameter
    icon_param = []
    if os.path.exists("icon.ico"):
        icon_param = ["--icon=icon.ico"]
        print("   ✅ Found icon.ico")
    else:
        print("   ⚠️ No icon.ico found (optional)")
    
    # Build command - simplified first
    cmd = [
        sys.executable, "-m", "PyInstaller",  # Use explicit Python module call
        "--noconfirm",
        "--onefile",
        "--clean",
        "--windowed",
        "--name=TubeRocket",
        *icon_param,
        # Essential hidden imports only
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk", 
        "--hidden-import=tkinter.scrolledtext",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=cryptography.fernet",
        "--hidden-import=requests",
        "--hidden-import=sqlite3",
        "--hidden-import=json",
        # Main script
        "tubeRocket_gui.py"
    ]
    
    # Add data files
    for src, dst in data_files:
        cmd.extend(["--add-data", f"{src};{dst}"])
    
    try:
        print("🔧 Running PyInstaller...")
        print(f"Command: {' '.join(cmd)}")
        
        # Run with more verbose output
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("\n✅ Build successful!")
            print("📁 Executable: dist/TubeRocket.exe")
            
            # Show file size
            exe_path = "dist/TubeRocket.exe"
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📦 File size: {size_mb:.1f} MB")
            
            # Create empty database file
            db_path = os.path.join("dist", "accounts.db")
            if not os.path.exists(db_path):
                try:
                    with open(db_path, 'w') as f:
                        pass
                    print("📄 Created empty accounts.db")
                except Exception as e:
                    print(f"⚠️ Could not create accounts.db: {e}")
            
            return True
        else:
            print(f"\n❌ PyInstaller failed with return code: {result.returncode}")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            return False
        
    except subprocess.TimeoutExpired:
        print("\n❌ Build timed out (took more than 5 minutes)")
        return False
    except FileNotFoundError as e:
        print(f"\n❌ File not found error: {e}")
        print("   Make sure Python and PyInstaller are properly installed")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during build: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def main():
    print("========================================")
    print("TubeRocket Build Tool")
    print("========================================")
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    clean_build()
    
    if not install_requirements():
        print("\n❌ Failed to install requirements!")
        input("\nPress Enter to exit...")
        return
    
    if build_exe():
        print("\n✨ Build completed successfully!")
        print("\n📋 What's included:")
        print("• TubeRocket.exe - Main executable (no console)")
        print("• accounts.db - Empty database file")
        print("• All features: Account management, Proxy support, Export/Import")
        print("\n💡 Ready to distribute!")
    else:
        print("\n❌ Build failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure all Python files are in the same directory")
        print("2. Try running as administrator")
        print("3. Check Windows Defender/Antivirus settings")
        print("4. Try building console version: python build_console.py")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
