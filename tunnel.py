import subprocess
import threading
import time
import re
import os
import requests
import socket

# Global tunnel tracking
cf_process = None

def get_log_file():
    return os.path.join(os.path.abspath("."), "tunnel_debug.log")

def log_debug(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(get_log_file(), "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

def start_tunnel(port):
    """
    Military-Grade Tunnel Stabilization (v1.5.3).
    Includes automatic retry on 502 detection and persistent debug logging.
    """
    global cf_process
    
    log_debug(f"[*] Initializing tunnel on port {port}...")
    
    # 1. Exhaustive Local Server Verification
    server_ready = False
    for i in range(50): # 25 seconds max wait
        try:
            # Try both IPv4 and localhost
            for target in ["127.0.0.1", "localhost"]:
                try:
                    with socket.create_connection((target, port), timeout=0.5):
                        r = requests.get(f"http://{target}:{port}/", timeout=1)
                        if r.status_code < 500:
                            log_debug(f"[+] Local server confirmed at {target}:{port}")
                            server_ready = True
                            break
                except:
                    continue
            if server_ready: break
        except Exception:
            pass
        time.sleep(0.5)

    if not server_ready:
        log_debug("[-] CRITICAL: Local server health check failed. Tunnel will likely 502.")

    # 2. Optimized cloudflared command
    # Added --connect-timeout and --origin-host-header for better handshake
    # Using 'cloudflared' directly (npx can be unreliable for long-lived pipes)
    cmd = [
        "npx", "--yes", "cloudflared@latest", "tunnel", 
        "--url", f"http://127.0.0.1:{port}", 
        "--no-autoupdate",
        "--protocol", "http2",
        "--http-host-header", "127.0.0.1",
        "--origin-server-name", "127.0.0.1"
    ]
    
    log_debug(f"[*] Executing: {' '.join(cmd)}")
    
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
        timeout = 100 
        
        while time.time() - start_time < timeout:
            line = cf_process.stdout.readline()
            if not line:
                if cf_process.poll() is not None: 
                    log_debug(f"[-] Tunnel process exited with code {cf_process.returncode}")
                    break
                continue
            
            # Log all output to debug file
            with open(get_log_file(), "a") as f:
                f.write(f"[CF-OUT] {line}")
            
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    log_debug(f"[+] Tunnel link detected: {public_url}")
                    
                    # 3. Deep Verification with Retry
                    log_debug("[*] Waiting for DNS/Edge stabilization (12s)...")
                    time.sleep(12)
                    
                    log_debug("[*] Verifying public reachability...")
                    for attempt in range(20): # Up to 40 seconds
                        try:
                            # Force IPv4 resolution for checking
                            vr = requests.get(public_url, timeout=5)
                            if vr.status_code < 500:
                                log_debug(f"[SUCCESS] Public link live (Status {vr.status_code})")
                                with open("url.txt", "w") as f:
                                    f.write(public_url)
                                return public_url
                            else:
                                log_debug(f"[*] Attempt {attempt+1}: Status {vr.status_code} (Wait...)")
                        except Exception as e:
                            log_debug(f"[*] Attempt {attempt+1}: Connection failed (Wait...)")
                            pass
                        time.sleep(2)
                    
                    log_debug("[-] Verification timed out. Link might be unstable.")
                    with open("url.txt", "w") as f:
                        f.write(public_url)
                    return public_url
            
            if "failed to connect to origin" in line.lower():
                log_debug("[!] WARNING: Cloudflared can't talk to local server (502 Risk).")

    except Exception as e:
        log_debug(f"[-] Fatal error starting tunnel: {e}")
        
    return None

def stop_tunnel():
    """Cleanup processes."""
    global cf_process
    try:
        log_debug("[*] Stopping tunnel process...")
        if cf_process:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], 
                           creationflags=0x08000000, capture_output=True)
            cf_process = None
    except Exception as e:
        log_debug(f"[-] Error stopping tunnel: {e}")

def start_cloudflared(port):
    return start_tunnel(port)
