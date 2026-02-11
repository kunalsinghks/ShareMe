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
    Indestructible Tunnel Startup (v1.5.2).
    Specifically targets DNS_PROBE_FINISHED_NXDOMAIN issues by forcing 
    extended propagation delays and using the most stable tunnel protocol.
    """
    global cf_process
    
    # 1. Broad Server Search: Try to reach the server on loopback
    print(f"[*] Probing local server on 127.0.0.1:{port}...")
    server_ready = False
    
    for i in range(40): # 20 seconds max wait
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
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

    # 2. Start Cloudflare Tunnel with forced stable protocol
    # Using 'cloudflared@latest' to ensure we have the newest DNS handling
    # We use 'http2' for Windows stability and '127.0.0.1' to bypass localhost issues
    cmd = [
        "npx", "--yes", "cloudflared@latest", "tunnel", 
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
                    print(f"[+] Tunnel link detected: {public_url}")
                    
                    # 3. CRITICAL: Solving NXDOMAIN / Propagation
                    # Some ISP DNS servers (like in India) are extremely slow to update
                    # We now force a 10s wait AND a triple-point verification
                    print("[*] Performing Deep DNS Stabilization (10s)...")
                    time.sleep(10)
                    
                    verified = False
                    print("[*] Verifying Global Edge Reachability...")
                    for _ in range(15): # Try for 30 more seconds
                        try:
                            # We use a real GET request to force DNS resolution
                            vr = requests.get(public_url, timeout=5)
                            if vr.status_code < 500:
                                print("[SUCCESS] Edge Reachable. Tunnel is fully live!")
                                verified = True
                                break
                        except Exception as e:
                            # print(f"[*] Waiting for DNS: {e}")
                            pass
                        time.sleep(2)
                    
                    if not verified:
                        print("[-] Warning: Domain exists but DNS propagation is still ongoing.")
                    
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
            
            if "failed to connect to origin" in line.lower():
                print("[!] Cloudflared handshake error. check server binding.")

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
