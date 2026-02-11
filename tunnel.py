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
    Highly Resilient Tunnel Startup (v1.5.0).
    Uses 127.0.0.1 for maximum loopback stability and avoids DNS/Proxy conflicts.
    """
    global cf_process
    
    # 1. Broad Server Search: Try to reach the server on loopback
    print(f"[*] Probing local server on 127.0.0.1:{port}...")
    server_ready = False
    
    # We check 127.0.0.1 explicitly
    for i in range(40): # 20 seconds max wait
        try:
            # Direct socket check first (fast)
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                # Now try HTTP check
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

    # 2. Optimized cloudflared command
    # Removed --http-host-header which can sometimes cause 502s if the origin doesn't expect it
    # Protocol 'http2' is used for stability
    cmd = [
        "npx", "--yes", "cloudflared", "tunnel", 
        "--url", f"http://127.0.0.1:{port}", 
        "--no-autoupdate",
        "--protocol", "http2"
    ]
    
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
        timeout = 90 
        
        while time.time() - start_time < timeout:
            line = cf_process.stdout.readline()
            if not line:
                if cf_process.poll() is not None: break
                continue
            
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    print(f"[+] Tunnel established: {public_url}")
                    
                    # 3. CRITICAL DNS HANDSHAKE
                    # We verify the public URL actually works before returning it
                    print("[*] Verifying public access link...")
                    verified = False
                    for _ in range(10): # Try for 20 seconds
                        try:
                            # Use a real request to verify the gateway is open
                            vr = requests.get(public_url, timeout=5)
                            if vr.status_code < 500:
                                print("[SUCCESS] Tunnel is fully live!")
                                verified = True
                                break
                        except:
                            pass
                        time.sleep(2)
                    
                    if not verified:
                        print("[-] Warning: Link generated but edge gateway is still returning errors.")
                    
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
            
            if "failed to connect to origin" in line.lower():
                print("[!] Tunnel connected but server handshake failed.")

    except Exception as e:
        print(f"Error starting tunnel: {e}")
        
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

def start_cloudflared(port):
    return start_tunnel(port)
