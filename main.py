import os
import time
import datetime
import mimetypes
from fastapi import FastAPI, HTTPException, Request, Query, Form, Response, Depends
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import config
import tunnel

import sys

# Path resolution for PyInstaller
def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")

BASE_PATH = get_base_path()

app = FastAPI(title="ShareME Server")

# Mount static files
static_path = os.path.join(BASE_PATH, "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

template_path = os.path.join(BASE_PATH, "templates")
templates = Jinja2Templates(directory=template_path)

# Configure shared base directory
# For simplicity, we just share everything inside the 'shared' folder created in config.py
SHARED_DIR = os.path.abspath("shared")
if not os.path.exists(SHARED_DIR):
    os.makedirs(SHARED_DIR)

PUBLIC_URL = None

def is_authenticated(request: Request):
    conf = config.load_config()
    required_password = conf.get("access_password")
    
    # If no password is set, everyone is authenticated
    if not required_password:
        return True
    
    # Check session cookie
    session_token = request.cookies.get("shareme_session")
    return session_token == required_password

def get_safe_path(requested_path: str):
    """Normalize and validate the path to prevent traversal attacks."""
    if not requested_path:
        return SHARED_DIR
    
    # Remove leading slashes/dots
    safe_suffix = requested_path.lstrip("/").lstrip("\\")
    full_path = os.path.abspath(os.path.join(SHARED_DIR, safe_suffix))
    
    # Ensure the path is within SHARED_DIR
    if not full_path.startswith(SHARED_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return full_path

def get_file_size_h(size_bytes):
    """Human readable file size."""
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
async def login(response: Response, password: str = Form(...)):
    conf = config.load_config()
    if password == conf.get("access_password"):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="shareme_session", value=password, httponly=True)
        return response
    return RedirectResponse(url="/login?error=Invalid+Password", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def list_files(request: Request, path: str = Query("")):
    if not is_authenticated(request):
        return RedirectResponse(url="/login")
        
    full_path = get_safe_path(path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Path not found")
    
    if os.path.isfile(full_path):
        return FileResponse(full_path)

    items = os.listdir(full_path)
    folders = []
    files = []
    
    for item in items:
        item_path = os.path.join(full_path, item)
        rel_path = os.path.relpath(item_path, SHARED_DIR)
        
        if os.path.isdir(item_path):
            folders.append({
                "name": item,
                "path": rel_path
            })
        else:
            stat = os.stat(item_path)
            files.append({
                "name": item,
                "path": rel_path,
                "size": get_file_size_h(stat.st_size),
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
            
    # Breadcrumbs
    breadcrumbs = []
    if path:
        parts = path.split(os.sep)
        curr_url = ""
        for p in parts:
            if not p: continue
            curr_url += p + os.sep
            breadcrumbs.append({"name": p, "url": f"/?path={curr_url}"})

    return templates.TemplateResponse("index.html", {
        "request": request,
        "folders": sorted(folders, key=lambda x: x['name'].lower()),
        "files": sorted(files, key=lambda x: x['name'].lower()),
        "public_url": PUBLIC_URL,
        "breadcrumbs": breadcrumbs
    })

@app.get("/download")
async def download_file(request: Request, path: str):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    full_path = get_safe_path(path)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=full_path,
        filename=os.path.basename(full_path),
        media_type='application/octet-stream'
    )

def start_tunnel():
    global PUBLIC_URL
    # We'll run the tunnel in a background thread so it doesn't block FastAPI
    def run():
        global PUBLIC_URL
        PUBLIC_URL = tunnel.start_localtunnel(8000)
    
    threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    import threading
    
    # Start the tunnel process
    start_tunnel()
    
    print(f"\n[*] Starting ShareME server on port 8000...")
    print(f"[*] Shared Directory: {SHARED_DIR}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
