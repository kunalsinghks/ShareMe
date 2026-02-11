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
    Highly Resilient Tunnel Startup (v1.4.8).
    Attempts to solve the 502 Bad Gateway by using robust origin resolution
    and ensuring the local server is fully alive.
    """
    global cf_process
    
    # 1. Broad Server Search: Try to reach the server on loopback
    print(f"[*] Probing local server on port {port}...")
    server_ready = False
    
    # Use 127.0.0.1 to avoid IPv6 issues during health check
    for _ in range(40): # 20 seconds max wait
        try:
            r = requests.get(f"http://127.0.0.1:{port}/", timeout=1)
            if r.status_code < 500:
                print(f"[+] Local server confirmed at 127.0.0.1:{port}")
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not server_ready:
        print("[-] Warning: Local server health check failed. Tunnel may 502.")

    # 2. Start Cloudflare Tunnel
    # We use 127.0.0.1 explicitly to bypass any 'localhost' resolution issues in 'cloudflared'
    # Adding --http-host-header to ensure 'cloudflared' correctly identifies the origin
    # We also use --protocol http2 for better stability on Windows
    cmd = [
        "npx", "--yes", "cloudflared", "tunnel", 
        "--url", f"http://127.0.0.1:{port}", 
        "--no-autoupdate",
        "--http-host-header", "127.0.0.1",
        "--protocol", "http2"
    ]
    
    try:
        # We must set bufsize=1 and universal_newlines=True to read lines effectively
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
        timeout = 90 # Increased timeout for slow paths
        
        while time.time() - start_time < timeout:
            line = cf_process.stdout.readline()
            if not line:
                # Check if process died
                if cf_process.poll() is not None:
                    print(f"[-] Tunnel process died with exit code {cf_process.returncode}")
                    break
                continue
            
            # Print for debug context if needed
            # print(f"[TUNNEL] {line.strip()}")
            
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    print(f"[+] Tunnel established: {public_url}")
                    # 3. DNS/Edge Buffer: Wait longer for the 502 to clear
                    # Some ISP/Firewall combinations take longer to route the first time
                    time.sleep(8) 
                    
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
            
            if "failed to connect to origin" in line.lower():
                print("[!] Cloudflared reporting origin connection failure...")

    except Exception as e:
        print(f"Error starting tunnel: {e}")
        
    return None

def stop_tunnel():
    """Silent process termination."""
    global cf_process
    try:
        if cf_process:
            # Use taskkill to kill the npx wrapper and the cloudflared process itself
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], 
                           creationflags=0x08000000, capture_output=True)
            cf_process = None
    except:
        pass

def start_cloudflared(port):
    return start_tunnel(port)
