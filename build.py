import subprocess
import sys
import os
import shutil

def clean_build():
    """Clean old build files"""
    print("🧹 Cleaning old build files...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    for pattern in files_to_clean:
        for file in os.glob.glob(pattern):
            os.remove(file)

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_build.txt"])

def build_exe():
    """Build the executable"""
    print("🚀 Building TubeRocket.exe...")
    
    # Files to include
    include_files = [
        "account_dialog.py",
        "database.py", 
        "proxy_manager.py",
        "tuberocket_worker.py"
    ]
    
    # Data files to bundle
    data_files = []
    if os.path.exists("encryption.key"):
        data_files.append(("encryption.key", "."))
    if os.path.exists("icon.ico"):
        icon_param = ["--icon=icon.ico"]
    else:
        icon_param = []
    
    # Build command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--clean",
        "--windowed",
        "--name=TubeRocket",
        *icon_param,
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk", 
        "--hidden-import=tkinter.scrolledtext",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=cryptography",
        "--hidden-import=cryptography.fernet",
        "--hidden-import=requests",
        "--hidden-import=sqlite3",
        "--hidden-import=threading",
        "--hidden-import=json",
        "--hidden-import=base64",
    ]
    
    # Add data files
    for src, dst in data_files:
        cmd.extend(["--add-data", f"{src};{dst}"])
    
    # Add main script
    cmd.append("tubeRocket_gui.py")
    
    try:
        # Copy all required files to build directory
        os.makedirs("build_temp", exist_ok=True)
        for file in include_files:
            shutil.copy(file, "build_temp")
        shutil.copy("tubeRocket_gui.py", "build_temp")
        
        # Run build from temp directory
        original_dir = os.getcwd()
        os.chdir("build_temp")
        subprocess.run(cmd, check=True)
        os.chdir(original_dir)
        
        # Move result back
        if not os.path.exists("dist"):
            os.makedirs("dist")
        shutil.move("build_temp/dist/TubeRocket.exe", "dist/TubeRocket.exe")
        
        # Cleanup
        shutil.rmtree("build_temp")
        print("\n✅ Build successful!")
        print("📁 Executable: dist/TubeRocket.exe")
        
        # Show file size
        size_mb = os.path.getsize("dist/TubeRocket.exe") / (1024 * 1024)
        print(f"📦 File size: {size_mb:.1f} MB")
        
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Run 'pip install -r requirements_build.txt'")
        print("2. Make sure all Python files are in the same directory")
        print("3. Try running with --console flag for debugging")
        return False
    
    return True

def main():
    clean_build()
    install_requirements()
    if build_exe():
        print("\n✨ Build completed successfully!")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
