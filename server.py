import os
import signal
import subprocess
import logging
import sqlite3
import glob
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

# Global process handle
crawler_process: Optional[subprocess.Popen] = None
LOG_FILE = "crawler.log"
DB_FILE = "products.db"

class ConfigPayload(BaseModel):
    filename: str
    content: str

@app.get("/")
def read_root():
    return FileResponse("ui/index.html")

@app.get("/api/status")
def get_status():
    global crawler_process
    
    # Check process status
    is_running = False
    pid = None
    if crawler_process:
        if crawler_process.poll() is None:
            is_running = True
            pid = crawler_process.pid
        else:
            crawler_process = None # Clean up if finished

    # Check process via ps if not tracked (e.g. started externally)
    # This ensures UI finds existing processes
    if not is_running:
        try:
            # Check for main.py or turbo.py
            for pattern in ["main.py --config", "turbo.py --config"]:
                try:
                    output = subprocess.check_output(["pgrep", "-f", pattern]).strip()
                    if output:
                        is_running = True
                        pid = int(output.split()[0])
                        break
                except subprocess.CalledProcessError:
                    continue
        except Exception:
            pass

    # Get DB Stats
    product_count = 0
    unique_skus = 0
    has_price = 0
    has_category = 0
    if os.path.exists(DB_FILE):
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM products")
            product_count = cur.fetchone()[0]
            cur.execute("SELECT count(DISTINCT sku) FROM products")
            unique_skus = cur.fetchone()[0]
            cur.execute("SELECT count(DISTINCT sku) FROM products WHERE price IS NOT NULL AND price > 0")
            has_price = cur.fetchone()[0]
            cur.execute("SELECT count(DISTINCT sku) FROM products WHERE category_path != '[]' AND category_path IS NOT NULL")
            has_category = cur.fetchone()[0]
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

    return {
        "running": is_running,
        "pid": pid,
        "product_count": product_count,
        "unique_skus": unique_skus,
        "has_price": has_price,
        "has_category": has_category
    }

@app.get("/api/logs")
def get_logs(lines: int = 50):
    if not os.path.exists(LOG_FILE):
        return PlainTextResponse("No logs found.")
    
    # Read last N lines
    try:
        # Use tail command for efficiency on mac
        output = subprocess.check_output(["tail", "-n", str(lines), LOG_FILE])
        return PlainTextResponse(output.decode("utf-8"))
    except Exception as e:
        return PlainTextResponse(f"Error reading logs: {str(e)}")

@app.post("/api/start")
def start_crawler(config_file: str = Body(..., embed=True)):
    global crawler_process
    
    # Don't start if already running
    status = get_status()
    if status["running"]:
        return {"status": "error", "message": "Crawler already running"}
    
    cmd = [
        "python3", "main.py",
        "--config", config_file,
        "--db", DB_FILE
    ]
    
    # Open log file for appending
    log_fd = open(LOG_FILE, "a")
    
    # partial command to match pgrep
    print(f"Starting: {' '.join(cmd)}")
    
    crawler_process = subprocess.Popen(
        cmd,
        stdout=log_fd,
        stderr=subprocess.STDOUT
    )
    
    return {"status": "started", "pid": crawler_process.pid}

@app.post("/api/stop")
def stop_crawler():
    global crawler_process
    status = get_status()
    
    if not status["running"]:
        return {"status": "ignored", "message": "Not running"}

    if status["pid"]:
        try:
            os.kill(status["pid"], signal.SIGTERM)
            return {"status": "stopped", "pid": status["pid"]}
        except Exception as e:
             return {"status": "error", "message": str(e)}
    
    return {"status": "error", "message": "No PID found"}

@app.get("/api/configs")
def list_configs():
    files = glob.glob("config/*.yaml")
    return {"files": files}

@app.get("/api/config/{filename}")
def get_config(filename: str):
    # Security check: ensure only filename, no path traversal
    safe_name = os.path.basename(filename)
    path = Path("config") / safe_name
    if path.exists():
        return {"content": path.read_text()}
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/config")
def save_config(payload: ConfigPayload):
    safe_name = os.path.basename(payload.filename)
    path = Path("config") / safe_name
    path.write_text(payload.content)
    return {"status": "saved"}

# Mount UI static files if needed, but we serve index directly
app.mount("/ui", StaticFiles(directory="ui"), name="ui")
