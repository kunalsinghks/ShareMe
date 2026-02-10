import subprocess
import threading
import time
import re
import os
import requests
import socket

# Global tunnel tracking
cf_process = None

def start_tunnel(port):
    """
    Fast Cloudflare Tunnel Startup.
    Returns the URL immediately once detected.
    """
    global cf_process
    
    print(f"[*] Starting Cloudflare Tunnel on port {port}...")
    
    # We use http2 protocol to bypass UDP issues and --no-autoupdate for speed
    cmd = ["npx", "--yes", "cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate", "--protocol", "http2"]
    
    try:
        cf_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            creationflags=0x08000000 # CREATE_NO_WINDOW
        )
        
        public_url = None
        start_time = time.time()
        timeout = 60 
        
        while time.time() - start_time < timeout:
            line = cf_process.stdout.readline()
            if not line: break
            
            line_str = line.strip()
            if "trycloudflare.com" in line_str:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line_str)
                if match:
                    public_url = match.group(0)
                    print(f"\n[!] Tunnel Created: {public_url}")
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
                    
            if "failed to connect to origin" in line_str.lower():
                print("[!] Waiting for local server connection...")

    except Exception as e:
        print(f"[-] Cloudflare startup failed: {e}")
        
    return None

def stop_tunnel():
    """Cleanup Cloudflare process."""
    global cf_process
    try:
        if cf_process:
            print("[*] Closing Tunnel...")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], capture_output=True)
            cf_process = None
    except:
        pass

# Maintain compatibility
def start_cloudflared(port):
    return start_tunnel(port)
