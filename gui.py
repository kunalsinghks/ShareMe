import os
import shutil
import threading
import sys
import webbrowser
import secrets
import string
import time
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import uvicorn
from PIL import Image, ImageTk, ImageDraw
import qrcode
import io
import pystray
from pystray import MenuItem as item

# Import our existing logic
import main
import config
import tunnel

# --- Premium Refined Palette ---
LIGHT_BG = "#FDFDFD"
LIGHT_SURFACE = "#F3F6FB"
LIGHT_SHADOW_DARK = "#D1D9E6"
LIGHT_SHADOW_LIGHT = "#FFFFFF"

DARK_BG = "#0B0E14"
DARK_SURFACE = "#151921"
DARK_SHADOW_DARK = "#000000"
DARK_SHADOW_LIGHT = "#232A35"

# Vibrant Accent Colors
BTN_PURPLE = "#6366F1"
BTN_PURPLE_HOVER = "#4F46E5"
BTN_SEC = "#2D3748"
BTN_SEC_HOVER = "#1A202C"

class ShareMEApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        # Window Setup
        self.title("ShareME v1.4.9 | Cloudflare P2P")
        self.geometry("1000x800")
        
        # Appearance - LIGHT MODE DEFAULT
        ctk.set_appearance_mode("light")
        self.main_font = "Outfit"

        # Configuration & State
        self.is_running = False
        self.public_url = "---"
        self.server_port = 8000
        
        conf = config.load_config()
        self.current_password = conf.get("access_password") or ""

        self.configure(fg_color=(LIGHT_BG, DARK_BG))

        # System Tray Support
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.create_tray_icon()

        # --- UI LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar = ctk.CTkFrame(self, width=320, border_width=0, corner_radius=0, fg_color=(LIGHT_SURFACE, DARK_SURFACE))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="ShareME.", font=ctk.CTkFont(family=self.main_font, size=38, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=40, pady=(70, 40))

        self.p_badge = ctk.CTkFrame(self.sidebar, fg_color=("#EEF2FF", "#1E1B4B"), corner_radius=12)
        self.p_badge.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        self.p_label = ctk.CTkLabel(self.p_badge, text="☁ CLOUDFLARE TUNNEL", text_color="#6366F1", font=ctk.CTkFont(family=self.main_font, size=11, weight="bold"))
        self.p_label.pack(pady=8)

        self.sec_box = ctk.CTkFrame(self.sidebar, corner_radius=25, border_width=1, border_color=(LIGHT_SHADOW_DARK, "#202020"), fg_color=(LIGHT_BG, DARK_BG))
        self.sec_box.grid(row=2, column=0, padx=25, pady=20, sticky="ew")
        
        self.sec_t = ctk.CTkLabel(self.sec_box, text="ACCESS PROTECTION", font=ctk.CTkFont(family=self.main_font, size=11, weight="bold"), text_color="gray50")
        self.sec_t.pack(pady=(20, 5))

        self.pass_entry = ctk.CTkEntry(self.sec_box, placeholder_text="No Password (Open)", height=45, border_width=0, corner_radius=12, fg_color=(LIGHT_SURFACE, DARK_SURFACE), font=ctk.CTkFont(family=self.main_font, size=14))
        self.pass_entry.insert(0, self.current_password)
        self.pass_entry.pack(padx=20, pady=10, fill="x")

        self.save_btn = ctk.CTkButton(self.sec_box, text="Apply Changes", command=self.update_config, height=40, corner_radius=12, font=ctk.CTkFont(family=self.main_font, weight="bold"), fg_color=BTN_SEC, hover_color=BTN_SEC_HOVER)
        self.save_btn.pack(padx=20, pady=(10, 20), fill="x")

        self.qr_card = ctk.CTkFrame(self.sidebar, corner_radius=25, border_width=1, border_color=(LIGHT_SHADOW_DARK, "#202020"), fg_color=(LIGHT_BG, DARK_BG))
        self.qr_label = ctk.CTkLabel(self.qr_card, text="")
        
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Dark Atmosphere", command=self.toggle_theme, font=ctk.CTkFont(family=self.main_font, size=13))
        self.theme_switch.deselect()
        self.theme_switch.grid(row=5, column=0, padx=40, pady=30, sticky="s")
        
        self.status_badge = ctk.CTkLabel(self.sidebar, text="● SYSTEM READY", text_color="gray50", font=ctk.CTkFont(family=self.main_font, size=12, weight="bold"))
        self.status_badge.grid(row=6, column=0, pady=(0, 40))
        self.sidebar.grid_rowconfigure(4, weight=1)

        # 2. Main Workspace
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=60, pady=60)
        self.main_view.grid_columnconfigure(0, weight=1)
        self.main_view.grid_rowconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 30))
        
        self.h_title = ctk.CTkLabel(self.top_bar, text="Filespace", font=ctk.CTkFont(family=self.main_font, size=32, weight="bold"))
        self.h_title.pack(side="left")

        self.start_btn = ctk.CTkButton(self.top_bar, text="START SHARING", width=180, height=55, corner_radius=20, font=ctk.CTkFont(family=self.main_font, size=15, weight="bold"), fg_color=BTN_PURPLE, hover_color=BTN_PURPLE_HOVER, command=self.toggle_server)
        self.start_btn.pack(side="right")

        self.list_container = ctk.CTkFrame(self.main_view, corner_radius=40, border_width=2, border_color=(LIGHT_SHADOW_DARK, DARK_SHADOW_DARK), fg_color=(LIGHT_BG, DARK_BG))
        self.list_container.grid(row=1, column=0, sticky="nsew")
        self.list_container.grid_columnconfigure(0, weight=1)
        self.list_container.grid_rowconfigure(0, weight=1)

        self.list_box = ctk.CTkTextbox(self.list_container, font=ctk.CTkFont(family=self.main_font, size=16), fg_color="transparent", text_color=("gray20", "gray80"), border_width=0)
        self.list_box.grid(row=0, column=0, padx=35, pady=35, sticky="nsew")

        self.action_bar = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.action_bar.grid(row=2, column=0, pady=(35, 0), sticky="ew")
        
        self.btn_files = ctk.CTkButton(self.action_bar, text="+ Add Files", width=140, height=50, corner_radius=18, fg_color=BTN_SEC, hover_color=BTN_SEC_HOVER, font=ctk.CTkFont(weight="bold"), command=self.add_files)
        self.btn_files.pack(side="left", padx=10)
        
        self.btn_folder = ctk.CTkButton(self.action_bar, text="+ Add Folder", width=140, height=50, corner_radius=18, fg_color=BTN_SEC, hover_color=BTN_SEC_HOVER, font=ctk.CTkFont(weight="bold"), command=self.add_folder)
        self.btn_folder.pack(side="left", padx=10)
        
        self.btn_reset = ctk.CTkButton(self.action_bar, text="Clean Up", width=100, height=50, corner_radius=18, fg_color="transparent", text_color="#ef4444", font=ctk.CTkFont(weight="bold"), command=self.clear_shared)
        self.btn_reset.pack(side="right", padx=10)
        
        # Performance Progress Bar
        self.add_progress = ctk.CTkProgressBar(self.main_view, height=4, corner_radius=0, progress_color=BTN_PURPLE)
        self.add_progress.grid(row=2, column=0, sticky="ew", pady=(85, 0))
        self.add_progress.set(0)

        self.url_area = ctk.CTkFrame(self.main_view, height=130, corner_radius=30, border_width=1, border_color="gray30", fg_color=(LIGHT_SURFACE, DARK_SURFACE))
        self.url_area.grid(row=3, column=0, pady=(45, 0), sticky="ew")
        
        self.url_display = ctk.CTkEntry(self.url_area, height=60, border_width=0, corner_radius=18, font=ctk.CTkFont(family=self.main_font, size=15), fg_color=(LIGHT_BG, DARK_BG))
        self.url_display.insert(0, "Public Access Link: Waiting for connection...")
        self.url_display.configure(state="readonly")
        self.url_display.pack(side="left", fill="x", expand=True, padx=20, pady=25)
        
        self.qr_btn = ctk.CTkButton(self.url_area, text="QR", width=60, height=50, corner_radius=18, font=ctk.CTkFont(weight="bold"), fg_color=BTN_SEC, hover_color=BTN_SEC_HOVER, command=self.show_qr)
        self.qr_btn.pack(side="right", padx=(5, 5), pady=25)

        self.open_btn = ctk.CTkButton(self.url_area, text="Open", width=90, height=50, corner_radius=18, font=ctk.CTkFont(weight="bold"), fg_color=BTN_PURPLE, hover_color=BTN_PURPLE_HOVER, command=self.open_link)
        self.open_btn.pack(side="right", padx=(5, 20), pady=25)

        self.copy_btn = ctk.CTkButton(self.url_area, text="Copy", width=80, height=50, corner_radius=18, font=ctk.CTkFont(weight="bold"), fg_color=BTN_SEC, hover_color=BTN_SEC_HOVER, command=self.copy_link)
        self.copy_btn.pack(side="right", padx=(20, 5), pady=25)

        self.refresh_list()

    def hide_window(self):
        self.withdraw()
        # Optionally show a notification
    
    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self):
        self.is_running = False
        tunnel.stop_tunnel()
        try:
            os.system("taskkill /F /IM python.exe /FI \"WINDOWTITLE ne ShareME*\" /T")
        except: pass
        self.tray.stop()
        self.destroy()
        sys.exit(0)

    def create_tray_icon(self):
        def on_clicked(icon, item):
            if str(item) == "Open ShareME":
                self.after(0, self.show_window)
            elif str(item) == "Exit Completely":
                self.after(0, self.quit_app)

        # Create a simple icon image
        image = Image.new('RGB', (64, 64), BTN_PURPLE)
        dc = ImageDraw.Draw(image)
        dc.ellipse((10, 10, 54, 54), fill=LIGHT_BG)
        
        menu = pystray.Menu(
            item('Open ShareME', on_clicked),
            item('Exit Completely', on_clicked)
        )
        self.tray = pystray.Icon("ShareME", image, "ShareME File Server", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def update_config(self):
        new_pw = self.pass_entry.get().strip()
        conf_data = config.load_config()
        conf_data["access_password"] = new_pw
        config.save_config(conf_data)
        self.status_badge.configure(text="● CONFIG UPDATED", text_color=BTN_PURPLE)
        self.after(2000, lambda: self.status_badge.configure(text=("● LIVE" if self.is_running else "● SYSTEM READY"), text_color=("#10b981" if self.is_running else "gray50")))

    def add_files(self):
        files = filedialog.askopenfilenames()
        if files:
            threading.Thread(target=self._bg_add_files, args=(files,), daemon=True).start()

    def _bg_add_files(self, files):
        self.start_btn.configure(state="disabled")
        total = len(files)
        for i, f in enumerate(files):
            self.process_path(f)
            self.after(0, lambda v=(i+1)/total: self.add_progress.set(v))
        self.after(0, self.refresh_list)
        self.after(500, lambda: self.add_progress.set(0))
        self.after(0, lambda: self.start_btn.configure(state="normal"))

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            threading.Thread(target=self._bg_add_folder, args=(folder,), daemon=True).start()

    def _bg_add_folder(self, folder):
        self.start_btn.configure(state="disabled")
        self.process_path(folder)
        self.after(0, self.refresh_list)
        self.after(0, lambda: self.start_btn.configure(state="normal"))

    def process_path(self, path):
        shared_dir = os.path.abspath("shared")
        if not os.path.exists(shared_dir): os.makedirs(shared_dir)
        name = os.path.basename(path)
        target = os.path.join(shared_dir, name)
        
        try:
            # INSTANT SHARING: Use Symbolic Links (requires developer mode or admin)
            # Fallback to hardlinks or copy if symlink fails
            if os.path.exists(target):
                if os.path.isdir(target): shutil.rmtree(target)
                else: os.unlink(target)
            
            try:
                # Try symlink first (instant, works for huge files)
                os.symlink(path, target, target_is_directory=os.path.isdir(path))
            except:
                # Fallback to copy if symlink fails (e.g. partition boundary)
                if os.path.isdir(path): shutil.copytree(path, target)
                else: shutil.copy2(path, target)
        except Exception as e: print(f"Error: {e}")

    def clear_shared(self):
        shared_dir = os.path.abspath("shared")
        if os.path.exists(shared_dir):
            try:
                for filename in os.listdir(shared_dir):
                    file_path = os.path.join(shared_dir, filename)
                    try:
                        if os.path.isfile(file_path): os.unlink(file_path)
                        elif os.path.isdir(file_path): shutil.rmtree(file_path)
                    except: pass
            except: pass
        self.refresh_list()

    def refresh_list(self):
        shared_dir = os.path.abspath("shared")
        if not os.path.exists(shared_dir): os.makedirs(shared_dir)
        items = os.listdir(shared_dir)
        self.list_box.configure(state="normal")
        self.list_box.delete("0.0", "end")
        if not items:
            self.list_box.insert("0.0", "The workspace is empty. Add files above.")
        else:
            self.list_box.insert("0.0", "CURRENTLY SHARING:\n" + ("—"*50) + "\n\n")
            for item in items: self.list_box.insert("end", f" • {item}\n")
        self.list_box.configure(state="disabled")

    def toggle_server(self):
        if not self.is_running: self.start_server()
        else: self.stop_server()

    def start_server(self):
        self.is_running = True
        self.title("ShareME v1.4.9 | Cloudflare P2P")
        self.start_btn.configure(text="STOP SHARING", fg_color="#ef4444", hover_color="#dc2626")
        self.status_badge.configure(text="● STARTING...", text_color=BTN_PURPLE)
        threading.Thread(target=lambda: uvicorn.run(main.app, host="0.0.0.0", port=8000, log_level="error"), daemon=True).start()
        
        def tunnel_watch():
            curr_url = tunnel.start_cloudflared(self.server_port)
            if curr_url and self.is_running: 
                self.public_url = curr_url
                self.after(0, lambda: self.update_url_box(curr_url))
                self.after(0, lambda: self.status_badge.configure(text="● VERIFYING...", text_color=BTN_PURPLE))
                def verify_dns():
                    for _ in range(30):
                        if not self.is_running: break
                        try:
                            r = requests.head(curr_url, timeout=5)
                            if r.status_code < 500:
                                self.after(0, lambda: self.status_badge.configure(text="● LIVE ONLINE", text_color="#10b981"))
                                return
                        except: pass
                        time.sleep(2)
                    self.after(0, lambda: self.status_badge.configure(text="● DNS SLOW / LIVE", text_color="#fbbf24"))
                threading.Thread(target=verify_dns, daemon=True).start()
            else:
                self.after(0, lambda: self.status_badge.configure(text="● ERROR", text_color="#ef4444"))
                self.after(0, lambda: self.update_url_box("Tunnel failed. Try restarting sharing."))
        threading.Thread(target=tunnel_watch, daemon=True).start()

    def stop_server(self):
        self.is_running = False
        self.start_btn.configure(text="START SHARING", fg_color=BTN_PURPLE, hover_color=BTN_PURPLE_HOVER)
        self.status_badge.configure(text="● SYSTEM READY", text_color="gray50")
        self.url_display.configure(state="normal")
        self.url_display.delete(0, "end")
        self.url_display.insert(0, "Public Access Link: Offline")
        self.url_display.configure(state="readonly")
        self.qr_card.grid_forget()
        tunnel.stop_tunnel()
        try:
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE ne ShareME*", "/T"], 
                           creationflags=0x08000000, capture_output=True)
        except: pass

    def update_url_box(self, url):
        self.url_display.configure(state="normal")
        self.url_display.delete(0, "end")
        if "http" in url:
            self.url_display.insert(0, f"Link Ready: {url} (Ready in 30s)")
        else:
            self.url_display.insert(0, url)
        self.url_display.configure(state="readonly")

    def copy_link(self):
        link = self.public_url
        if "http" in link: 
            self.clipboard_clear()
            self.clipboard_append(link)
            self.status_badge.configure(text="● LINK COPIED", text_color=BTN_PURPLE)
            self.after(2000, lambda: self.status_badge.configure(text=("● LIVE ONLINE" if self.is_running else "● SYSTEM READY"), text_color=("#10b981" if self.is_running else "gray50")))

    def open_link(self):
        link = self.public_url
        if "http" in link: webbrowser.open(link)

    def show_qr(self):
        if not self.public_url or "http" not in self.public_url: return
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(self.public_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((220, 220), Image.Resampling.LANCZOS)
        self.qr_img = ImageTk.PhotoImage(img)
        self.qr_label.configure(image=self.qr_img)
        self.qr_label.pack(padx=20, pady=20)
        self.qr_card.grid(row=3, column=0, padx=25, pady=10, sticky="ew")

if __name__ == "__main__":
    app = ShareMEApp()
    app.mainloop()
