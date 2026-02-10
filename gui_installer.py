import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
import sys
import ctypes
from win32com.client import Dispatch

# Settings
APP_NAME = "ShareMe"
VERSION = "1.2.7"
ICON_NAME = "favicon.ico"
FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_HEADER = ("Segoe UI", 22, "bold")

class ShareMeInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{VERSION} Setup")
        self.root.geometry("640x500")
        self.root.configure(bg="#ffffff")
        self.root.resizable(False, False)
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=FONT_MAIN, padding=10, borderwidth=0)
        self.style.map("TButton", background=[('active', '#818cf8'), ('!disabled', '#6366f1')], foreground=[('!disabled', 'white')])
        self.style.configure("TLabel", font=FONT_MAIN, background="#ffffff")
        self.style.configure("Header.TLabel", font=FONT_HEADER, background="#6366f1", foreground="white")
        self.style.configure("Horizontal.TProgressbar", thickness=20, borderwidth=0, troughcolor="#f3f4f6", background="#6366f1")

        # State
        self.install_path = tk.StringVar(value=os.path.join(os.environ['LOCALAPPDATA'], APP_NAME))
        self.create_desktop_icon = tk.BooleanVar(value=True)

        self.setup_ui()

    def setup_ui(self):
        # Header area
        self.header_frame = tk.Frame(self.root, bg="#6366f1", height=80)
        self.header_frame.pack(fill="x")
        
        tk.Label(self.header_frame, text=f"Install {APP_NAME} v{VERSION}", 
                 fg="white", bg="#6366f1", font=("Outfit", 20, "bold")).pack(pady=20, padx=30, side="left")

        # Content area
        self.content = tk.Frame(self.root, padx=40, pady=30)
        self.content.pack(fill="both", expand=True)

        tk.Label(self.content, text="Choose installation folder:", font=("Outfit", 11, "bold")).pack(anchor="w")
        
        path_frame = tk.Frame(self.content)
        path_frame.pack(fill="x", pady=(5, 20))
        
        tk.Entry(path_frame, textvariable=self.install_path, font=("Outfit", 10), width=50).pack(side="left", padx=(0, 10))
        ttk.Button(path_frame, text="Browse...", command=self.browse_path).pack(side="left")

        tk.Label(self.content, text="Setup options:", font=("Outfit", 11, "bold")).pack(anchor="w")
        tk.Checkbutton(self.content, text="Create desktop shortcut", variable=self.create_desktop_icon, 
                       font=("Outfit", 10), pady=10).pack(anchor="w")

        # Footer / Progress
        self.footer = tk.Frame(self.root, pady=20, padx=40)
        self.footer.pack(fill="x", side="bottom")
        
        self.progress = ttk.Progressbar(self.footer, length=400, mode='determinate')
        
        self.install_btn = ttk.Button(self.footer, text="Install Now", command=self.start_installation)
        self.install_btn.pack(side="right")
        
        self.cancel_btn = ttk.Button(self.footer, text="Cancel", command=self.root.quit)
        self.cancel_btn.pack(side="right", padx=10)

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.install_path.set(path)

    def start_installation(self):
        self.install_btn.config(state="disabled")
        self.cancel_btn.config(state="disabled")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 20))
        
        threading.Thread(target=self.run_install, daemon=True).start()

    def run_install(self):
        try:
            target_dir = self.install_path.get()
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # Fix path issue: Use relative path to installer location
            base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
            src_dir = os.path.join(base_path, "ShareME")
            
            # If ShareME folder isn't found, look for files in same dir (Portable mode)
            if not os.path.exists(src_dir):
                src_dir = base_path

            files = [f for f in os.listdir(src_dir) if f not in ["ShareMe_Setup.exe", "gui_installer.py", "windows_installer.py"]]
            total = len(files)
            
            for i, item in enumerate(files):
                src_path = os.path.join(src_dir, item)
                dst_path = os.path.join(target_dir, item)
                
                if os.path.isdir(src_path):
                    if os.path.exists(dst_path): shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
                
                self.root.after(0, lambda v=int((i+1)/total*100): self.progress.set(v))
            
            # Create Shortcut
            if self.create_desktop_icon.get():
                exe_path = os.path.join(target_dir, "ShareME.exe")
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                self.create_shortcut(exe_path, os.path.join(desktop, f"{APP_NAME}.lnk"), exe_path)

            self.root.after(0, self.finish_install)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Installation failed: {str(e)}"))
            self.root.after(0, lambda: self.root.quit())

    def create_shortcut(self, target, shortcut_path, icon_path):
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = icon_path
        shortcut.save()

    def finish_install(self):
        messagebox.showinfo("Success", f"{APP_NAME} has been installed successfully!")
        self.root.quit()

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Optional: Force admin if needed
        pass
    
    root = tk.Tk()
    app = ShareMeInstaller(root)
    root.mainloop()
