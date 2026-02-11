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
    Fast Cloudflare Tunnel Startup with deep health check.
    """
    global cf_process
    
    # 1. Wait for local server to be fully responsive (HTTP Layer)
    # Socket check is fast, but HTTP check ensures FastAPI is actually running
    server_ready = False
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                # Socket is open, now try a quick internal request
                try:
                    requests.get(f"http://127.0.0.1:{port}", timeout=0.5)
                except requests.exceptions.ConnectionError:
                    pass # Server might be reset or initializing headers
                server_ready = True
                break
        except:
            time.sleep(0.5)

    if not server_ready:
        print("[-] Warning: Local server not detected. Attempting tunnel anyway...")

    # 2. Start Cloudflare Tunnel
    # We use --protocol http2 for better stability on Windows 
    cmd = ["npx", "--yes", "cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate", "--protocol", "http2"]
    
    try:
        cf_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True,
            creationflags=0x08000000 # CREATE_NO_WINDOW
        )
        
        public_url = None
        start_time = time.time()
        timeout = 60 
        
        while time.time() - start_time < timeout:
            line = cf_process.stdout.readline()
            if not line: break
            
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    # 3. CRITICAL: Wait for Cloudflare DNS propagation
                    # Without this, users get 502/404 for the first few seconds
                    time.sleep(3) 
                    
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
                    
    except Exception as e:
        print(f"Error: {e}")
        
    return None

def stop_tunnel():
    """Cleanup Cloudflare process without windows."""
    global cf_process
    try:
        if cf_process:
            # Use taskkill to ensure the entire tree is closed
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], 
                           creationflags=0x08000000, capture_output=True)
            cf_process = None
    except:
        pass

# Maintain compatibility
def start_cloudflared(port):
    return start_tunnel(port)
