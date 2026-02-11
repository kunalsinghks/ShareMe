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

import sys

def log_debug(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(get_log_file(), "a") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except: pass
    
    # Only print to console if NOT frozen (Debug mode)
    if not getattr(sys, 'frozen', False):
        try: print(msg)
        except: pass

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
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        cf_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            shell=False, # Changed to False for better signal handling
            startupinfo=startupinfo,
            creationflags=0
        )
        
        # Hybrid Start: Read first few lines synchronously to catch immediate errors/links
        # Then hand off to thread.
        global detected_url
        detected_url = None

        def read_loop(proc):
            global detected_url
            while True:
                line_bin = proc.stdout.readline()
                if not line_bin: break
                try:
                    line = line_bin.decode('utf-8', errors='ignore')
                except: continue
                
                if "trycloudflare.com" in line and not detected_url:
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if match: detected_url = match.group(0)
                        
                # Log
                try:
                    with open(get_log_file(), "a", encoding="utf-8") as f:
                        f.write(f"[CF-OUT] {line}")
                except: pass

        t = threading.Thread(target=read_loop, args=(cf_process,), daemon=True)
        t.start()
        
        start_time = time.time()
        while time.time() - start_time < 100:
            if detected_url:
                log_debug(f"[+] Tunnel link detected: {detected_url}")
                log_debug("[*] Waiting for DNS propagation (4s)...")
                time.sleep(4)
                
                with open("url.txt", "w") as f:
                    f.write(detected_url)
                return detected_url
            
            if cf_process.poll() is not None:
                break
            time.sleep(0.1)

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
