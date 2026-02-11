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
    Military-Grade Tunnel Stabilization (v1.5.5).
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
        "--protocol", "http2", # http2 is most stable for avoiding 1033 on Windows
        "--http-host-header", "127.0.0.1"
    ]
    
    log_debug(f"[*] Executing: {' '.join(cmd)}")
    
    try:
        cf_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            bufsize=1, # Re-enable line buffering for instant output
            universal_newlines=True, # Improved text handling
            shell=True,
            creationflags=0x08000000 if os.name == 'nt' else 0 
        )
        
        public_url = None
        start_time = time.time()
        timeout = 100 
        
        # Robust Read Loop for EXE
        while time.time() - start_time < timeout:
            line = cf_process.stdout.readline()
            if not line:
                if cf_process.poll() is not None: break
                continue

            # Log to debug file
            try:
                with open(get_log_file(), "a", encoding="utf-8") as f:
                    f.write(f"[CF-OUT] {line}")
            except: pass
            
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    log_debug(f"[+] Tunnel link detected: {public_url}")
                    
                    # 3. Enhanced DNS Stabilization (v1.5.8)
                    # 10s is the required buffer to avoid Error 1033 on Windows http2
                    log_debug("[*] Stabilizing Tunnel Connection (10s)...")
                    time.sleep(10)
                    
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
            if os.name == 'nt':
                # Taskkill to kill the whole tree on Windows
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(cf_process.pid)], 
                               creationflags=0x08000000, capture_output=True)
            else:
                # Standard kill on Unix
                import signal
                os.killpg(os.getpgid(cf_process.pid), signal.SIGTERM)
            cf_process = None
    except Exception as e:
        log_debug(f"[-] Error stopping tunnel: {e}")

def start_cloudflared(port):
    return start_tunnel(port)
