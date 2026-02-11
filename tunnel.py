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
    Highly Resilient Tunnel Startup (v1.4.6).
    Uses 127.0.0.1 for origin to bypass 'localhost' resolution bugs.
    """
    global cf_process
    
    # 1. Broad Server Search: Try to reach the server on loopback
    print(f"[*] Probing local server on port {port}...")
    server_ready = False
    for _ in range(30): # 15 seconds max wait
        try:
            # We check 127.0.0.1 regardless of binding (0.0.0.0 includes 127.0.0.1)
            r = requests.get(f"http://127.0.0.1:{port}", timeout=1)
            if r.status_code < 500:
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not server_ready:
        print("[-] Warning: Local server health check failed. Attempting tunnel anyway...")

    # 2. Optimized cloudflared command
    # Added --http-host-header to ensure the server sees the correct host if it cares
    # sticking to 127.0.0.1 as it's the most reliable origin address
    cmd = [
        "npx", "--yes", "cloudflared", "tunnel", 
        "--url", f"http://127.0.0.1:{port}", 
        "--no-autoupdate",
        "--http-host-header", "127.0.0.1"
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
                    # 3. DNS Buffer: Allow more time for initial handshake
                    time.sleep(6) 
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
            
            # Real-time connectivity debug
            if "failed to connect to origin" in line.lower():
                print("[!] Tunnel connected but server handshake failed. Retrying origin...")

    except Exception as e:
        print(f"Error: {e}")
        
    return None

def stop_tunnel():
    """Silent process termination."""
    global cf_process
    try:
        if cf_process:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], 
                           creationflags=0x08000000, capture_output=True)
            cf_process = None
    except:
        pass

# Maintain compatibility
def start_cloudflared(port):
    return start_tunnel(port)
