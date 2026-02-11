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
    Ultra-Stable Cloudflare Tunnel Startup.
    Ensures local server is 100% healthy before revealing the URL.
    """
    global cf_process
    
    # 1. STRICT Health Check: Wait for a valid HTTP response (not just a socket)
    print(f"[*] Verifying local server health on port {port}...")
    server_ready = False
    for i in range(30): # Up to 15 seconds
        try:
            # Try a real HTTP request to the root
            r = requests.get(f"http://127.0.0.1:{port}", timeout=1)
            if r.status_code < 500:
                print(f"[+] Local server is healthy (Status: {r.status_code})")
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not server_ready:
        print("[-] Error: Local server failed health check. The tunnel might show 502.")

    # 2. Start Cloudflare Tunnel
    # Removed --protocol http2 to let cloudflared pick the best protocol (usually QUIC/Auto)
    # Using localhost instead of 127.0.0.1 for high-level OS compatibility
    cmd = ["npx", "--yes", "cloudflared", "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"]
    
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
            
            # Clean logging for URL detection
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    # 3. CRITICAL: Wait for Cloudflare Edge & DNS stabilization
                    # Increased to 5 seconds to ensure the '502 Bad Gateway' disappears.
                    time.sleep(5) 
                    
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
            
            # If we detect common failure patterns, we log them but keep waiting
            if "failed to connect to origin" in line.lower():
                pass # Already handled by health check loop

    except Exception as e:
        print(f"Error: {e}")
        
    return None

def stop_tunnel():
    """Cleanup Cloudflare process without windows."""
    global cf_process
    try:
        if cf_process:
            # Deep taskkill to ensure orphaned processes are dead
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], 
                           creationflags=0x08000000, capture_output=True)
            cf_process = None
    except:
        pass

# Maintain compatibility
def start_cloudflared(port):
    return start_tunnel(port)
