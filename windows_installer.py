import os
import sys
import shutil
import ctypes
from win32com.client import Dispatch

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_shortcut(target, shortcut_path, icon_path):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.IconLocation = icon_path
    shortcut.save()

def install():
    print("--- ShareMe Windows Installer ---")
    
    # Default install location: %AppData%\ShareMe
    default_dir = os.path.join(os.environ['LOCALAPPDATA'], "ShareMe")
    install_dir = input(f"Choose install location [{default_dir}]: ").strip() or default_dir
    
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
    
    print(f"Installing to {install_dir}...")
    
    # In a real scenario, this script would be bundled with the files.
    # For now, we'll assume we're running from the 'dist' folder or source.
    src_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Copy files
    for item in os.listdir(src_dir):
        src_path = os.path.join(src_dir, item)
        dst_path = os.path.join(install_dir, item)
        if item == "install.exe" or item == ".git": continue
        
        if os.path.isdir(src_path):
            if os.path.exists(dst_path): shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)
            
    # Create Shortcut
    exe_path = os.path.join(install_dir, "ShareME.exe")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    create_shortcut(exe_path, os.path.join(desktop, "ShareMe.lnk"), exe_path)
    
    print("\n[✓] Installation Complete!")
    print(f"Shortcuts created on Desktop.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    install()
