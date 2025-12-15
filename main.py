from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import subprocess
import os
from datetime import datetime
import threading
import queue

processes = {}
log_content = []
log_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_message("Starting Spotify Logger Web Application...")
    log_message("Server running at http://127.0.0.1:8000")
    yield
    log_message("Application shutting down, stopping all scripts...")
    for script_name, proc in list(processes.items()):
        if proc.poll() is None:
            log_message(f"Stopping {script_name}...")
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            except Exception as e:
                log_message(f"Error stopping {script_name}: {e}")


app = FastAPI(lifespan=lifespan)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    with log_lock:
        log_content.append(formatted_msg)
        if len(log_content) > 1000:  # Increased from 500 to keep more logs
            log_content.pop(0)
    print(formatted_msg)  # Also print to console for debugging


def read_process_output(proc, script_name):
    """Read output from subprocess and log each line immediately"""
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                # Check if process has ended
                if proc.poll() is not None:
                    break
                continue
            
            # Strip whitespace and log
            line = line.strip()
            if line:
                log_message(f"[{script_name}] {line}")
                
    except Exception as e:
        log_message(f"[{script_name}] Error reading output: {e}")
    finally:
        log_message(f"[{script_name}] Process ended (exit code: {proc.poll()})")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found in static folder</h1>", status_code=500)


@app.post("/run-script/{script_name}")
async def run_script(script_name: str):
    
    if script_name not in ["log.py", "logger.py"]:
        log_message(f"Invalid script name: {script_name}")
        return JSONResponse(
            content={"status": "error", "message": f"Invalid script: {script_name}"},
            status_code=400
        )
    
    if script_name in processes:
        proc = processes[script_name]
        if proc.poll() is None:
            log_message(f"{script_name} is already running (PID: {proc.pid})")
            return JSONResponse(
                content={"status": "info", "message": f"{script_name} is already running"}
            )
    
    if not os.path.exists(script_name):
        log_message(f"Script not found: {script_name}")
        return JSONResponse(
            content={"status": "error", "message": f"Script '{script_name}' not found"},
            status_code=404
        )
    
    try:
        log_message(f"Starting {script_name}...")
        
        # Use PYTHONUNBUFFERED to disable output buffering
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        proc = subprocess.Popen(
            ["python", "-u", script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,  # Unbuffered
            env=env
        )
        
        processes[script_name] = proc
        
        # Start output reader thread
        thread = threading.Thread(
            target=read_process_output,
            args=(proc, script_name),
            daemon=True
        )
        thread.start()
        
        log_message(f"✓ Started {script_name} (PID: {proc.pid})")
        log_message(f"[{script_name}] Watching for output...")
        
        return JSONResponse(
            content={"status": "success", "message": f"Started {script_name}", "pid": proc.pid}
        )
        
    except Exception as e:
        log_message(f"Error starting {script_name}: {e}")
        import traceback
        log_message(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            content={"status": "error", "message": f"Error: {str(e)}"},
            status_code=500
        )


@app.post("/stop-script/{script_name}")
async def stop_script(script_name: str):
    
    if script_name not in processes:
        log_message(f"Script {script_name} is not running")
        return JSONResponse(
            content={"status": "info", "message": f"{script_name} is not running"}
        )
    
    proc = processes[script_name]
    
    if proc.poll() is not None:
        log_message(f"Script {script_name} has already stopped")
        del processes[script_name]
        return JSONResponse(
            content={"status": "info", "message": f"{script_name} has already stopped"}
        )
    
    try:
        log_message(f"Stopping {script_name} (PID: {proc.pid})...")
        
        proc.terminate()
        
        try:
            proc.wait(timeout=5)
            log_message(f"✓ Stopped {script_name}")
        except subprocess.TimeoutExpired:
            log_message(f"Force killing {script_name}...")
            proc.kill()
            proc.wait()
            log_message(f"✓ Force stopped {script_name}")
        
        del processes[script_name]
        return JSONResponse(
            content={"status": "success", "message": f"Stopped {script_name}"}
        )
        
    except Exception as e:
        log_message(f"Error stopping {script_name}: {e}")
        return JSONResponse(
            content={"status": "error", "message": f"Error: {str(e)}"},
            status_code=500
        )


@app.get("/get-updates")
async def get_updates():
    with log_lock:
        # Get last 100 log entries for display
        display_logs = log_content[-100:] if len(log_content) > 100 else log_content
        return JSONResponse(
            content={
                "logs": "\n".join(display_logs) if display_logs else "No logs yet. Click a button to run a script.",
                "timestamp": datetime.now().isoformat(),
                "total_logs": len(log_content)
            }
        )


@app.post("/clear-log")
async def clear_log():
    with log_lock:
        log_content.clear()
    log_message("Log cleared")
    return JSONResponse(
        content={"status": "success", "message": "Log cleared"}
    )


@app.get("/status")
async def get_status():
    status = {}
    scripts_to_remove = []
    
    for script_name, proc in processes.items():
        if proc.poll() is None:
            status[script_name] = {"running": True, "pid": proc.pid}
        else:
            status[script_name] = {"running": False, "pid": None}
            scripts_to_remove.append(script_name)
    
    for script_name in scripts_to_remove:
        del processes[script_name]
    
    return JSONResponse(content=status)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)