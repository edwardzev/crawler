import os
import signal
import subprocess
import logging
import sqlite3
import glob
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
import requests
import json
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuration
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = "app1tMmtuC7BGfJLu"
AIRTABLE_TABLE_NAME = "Orders"
AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
if CLOUDINARY_URL:
    try:
        clean_url = CLOUDINARY_URL.replace("cloudinary://", "")
        creds, cloud_name = clean_url.split("@")
        api_key, api_secret = creds.split(":")
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
    except Exception as e:
        print(f"Warning: Failed to configure Cloudinary: {e}")


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

@app.post("/api/order/create")
def create_order():
    """Step 1: Create a draft order in Airtable to get an ID."""
    if not AIRTABLE_PAT:
        raise HTTPException(status_code=500, detail="AIRTABLE_PAT not set")

    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    
    # Initial draft record
    payload = {
        "fields": {
        }
    }
    
    try:
        r = requests.post(AIRTABLE_API_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return {"order_id": data["id"]}
    except Exception as e:
        print(f"Airtable Create Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@app.post("/api/order/add-item")
async def add_order_item(
    order_id: str = Form(...),
    slot_index: int = Form(...),
    quantity: int = Form(...),
    width: float = Form(...),
    logo: UploadFile = File(...),
    mockup: UploadFile = File(...),
    product_title: str = Form(...),
    sku: str = Form(...),
    variant_type: str = Form(None),
    variant_value: str = Form(None),
    variant_label: str = Form(None)
):
    """Step 2: Upload files to Cloudinary and update specific slot in Airtable."""
    if slot_index < 1 or slot_index > 5:
        raise HTTPException(status_code=400, detail="Slot index must be 1-5")

    # 1. Upload to Cloudinary under orders/<ORDER_ID>/item_<SLOT_NUMBER>/
    base_folder = f"orders/{order_id}/item_{slot_index}"
    
    try:
        # Upload Logo
        logo_content = await logo.read()
        logo_res = cloudinary.uploader.upload(
            logo_content,
            folder=base_folder,
            public_id="logo",
            resource_type="image",
            overwrite=True
        )
        logo_url = logo_res.get("secure_url")

        # Upload Mockup
        mockup_content = await mockup.read()
        mockup_res = cloudinary.uploader.upload(
            mockup_content,
            folder=base_folder,
            public_id="mockup",
            resource_type="image",
            overwrite=True
        )
        mockup_url = mockup_res.get("secure_url")
        
    except Exception as e:
        print(f"Cloudinary Upload Error: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # 2. Update Airtable Slot
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    
    # Exact mapping based on spec
    # Standardized: Always use "Width N cm"
    width_field = f"Width {slot_index} cm"
    
    fields = {
        f"Graphic {slot_index}": [{"url": logo_url}],
        f"Mockup {slot_index}": [{"url": mockup_url}],
        width_field: width,
        f"Number {slot_index}": quantity
    }
    
    # Notes to Design: Structured format per requirements
    # Format:
    # [PRODUCT]
    # SKU: <sku>
    # Name: <product name>
    # Variant: <color or "N/A">
    # 
    # [GRAPHIC]
    # Slot: <N>
    # Width: <cm>
    # Quantity: <qty>
    
    try:
        r_get = requests.get(f"{AIRTABLE_API_URL}/{order_id}", headers=headers)
        r_get.raise_for_status()
        current_data = r_get.json()
        old_notes = current_data.get("fields", {}).get("Notes to Design", "")
        
        # Build structured entry
        variant_str = "N/A"
        if variant_type and variant_value and variant_label:
            variant_str = f"{variant_label} ({variant_value})"
        
        new_entry = f"""[PRODUCT]
SKU: {sku}
Name: {product_title}
Variant: {variant_str}

[GRAPHIC]
Slot: {slot_index}
Width: {width} cm
Quantity: {quantity}
"""
        
        # Append with separator
        separator = "\n" + "="*40 + "\n"
        if old_notes.strip():
            fields["Notes to Design"] = old_notes + separator + new_entry
        else:
            fields["Notes to Design"] = new_entry
    except:
        # Fallback if GET fails
        variant_str = "N/A"
        if variant_type and variant_value and variant_label:
            variant_str = f"{variant_label} ({variant_value})"
        
        fields["Notes to Design"] = f"""[PRODUCT]
SKU: {sku}
Name: {product_title}
Variant: {variant_str}

[GRAPHIC]
Slot: {slot_index}
Width: {width} cm
Quantity: {quantity}
"""

    try:
        r = requests.patch(f"{AIRTABLE_API_URL}/{order_id}", headers=headers, json={"fields": fields})
        r.raise_for_status()
        return {"status": "success", "slot": slot_index}
    except Exception as e:
        print(f"Airtable Update Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update slot: {str(e)}")

@app.post("/api/order/finalize")
def finalize_order(
    order_id: str = Body(..., embed=True),
    job_name: str = Body(..., embed=True),
    deadline: str = Body(..., embed=True),
    method: str = Body(..., embed=True),
    notes: str = Body(None, embed=True),
    final_check: bool = Body(..., embed=True)
):
    """Step 3: Finalize order-level data."""
    if not AIRTABLE_PAT:
        raise HTTPException(status_code=500, detail="AIRTABLE_PAT not set")

    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    
    fields = {
        "Job Name": job_name,
        "Deadline": deadline,
        "Method": method,
        "Notes": notes,
        "Final check": final_check
    }
    
    try:
        r = requests.patch(f"{AIRTABLE_API_URL}/{order_id}", headers=headers, json={"fields": fields})
        r.raise_for_status()
        return {"status": "success"}
    except Exception as e:
        print(f"Airtable Finalize Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to finalize: {str(e)}")


# Mount UI static files if needed, but we serve index directly
app.mount("/ui", StaticFiles(directory="ui"), name="ui")
