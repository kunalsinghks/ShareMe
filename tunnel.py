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
    Ultra-Stable Cloudflare Tunnel Startup (v1.4.5).
    Focuses on IPv4 connectivity and explicit origin resolution.
    """
    global cf_process
    
    # 1. Wait for local server to be fully responsive (IPv4)
    print(f"[*] Verifying local server on 127.0.0.1:{port}...")
    server_ready = False
    for i in range(20):
        try:
            # Using 127.0.0.1 explicitly to avoid IPv6 [::1] conflicts
            r = requests.get(f"http://127.0.0.1:{port}", timeout=1)
            if r.status_code < 500:
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not server_ready:
        print("[-] Warning: Local server not responding on 127.0.0.1. Tunnel may fail.")

    # 2. Start Cloudflare Tunnel
    # Protocol 'http2' is significantly more stable on Windows than default 'quic'
    # Using 127.0.0.1 instead of localhost to prevent IPv6 mismatch (::1 vs 127.0.0.1)
    cmd = [
        "npx", "--yes", "cloudflared", "tunnel", 
        "--url", f"http://127.0.0.1:{port}", 
        "--no-autoupdate", 
        "--protocol", "http2"
    ]
    
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
                    # 3. DNS/Edge Propagation Buffer
                    # 5 seconds is the sweet spot for trial tunnels to stabilize
                    time.sleep(5) 
                    
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
            
            if "failed to connect to origin" in line.lower():
                # If we see this, we might need to retry or log it
                pass

    except Exception as e:
        print(f"Error: {e}")
        
    return None

def stop_tunnel():
    """Cleanup Cloudflare process tree."""
    global cf_process
    try:
        if cf_process:
            # Use taskkill to kill the npx wrapper and the cloudflared process itself
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], 
                           creationflags=0x08000000, capture_output=True)
            cf_process = None
    except:
        pass

# Maintain compatibility
def start_cloudflared(port):
    return start_tunnel(port)
