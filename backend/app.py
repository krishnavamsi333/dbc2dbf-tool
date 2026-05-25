import os
import uuid
import sys
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Allow imports from backend/ when running as: python backend/app.py
sys.path.insert(0, str(Path(__file__).parent))

from validator import validate_dbc_file, ValidationError
from cleaner import clean_dbc_file
from converter import convert_dbc_to_dbf

# Resolve frontend path relative to this file (works from any cwd)
BACKEND_DIR  = Path(__file__).parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

app = FastAPI(title="DBC → DBF Converter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend assets (style.css, script.js)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

UPLOAD_FOLDER = tempfile.gettempdir()
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def check_dbc(filename: str):
    if not filename.lower().endswith(".dbc"):
        raise HTTPException(status_code=400, detail="File must be a .dbc file")


# ── Frontend ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the web UI"""
    html_file = FRONTEND_DIR / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "dbc2dbf-converter"}


# ── Validate ──────────────────────────────────────────────────────────────────

@app.post("/api/validate")
async def validate(file: UploadFile = File(...)):
    check_dbc(file.filename)

    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")

    tmp_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{file.filename}")
    try:
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        result = validate_dbc_file(tmp_path)
        return {"success": True, "validation": result}

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Convert ───────────────────────────────────────────────────────────────────

@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    clean: str = Form(default="true"),
):
    check_dbc(file.filename)

    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")

    do_clean = clean.lower() == "true"
    base_name = Path(file.filename).stem
    job_id = str(uuid.uuid4())

    tmp_input   = os.path.join(UPLOAD_FOLDER, f"{job_id}_input_{file.filename}")
    tmp_cleaned = os.path.join(UPLOAD_FOLDER, f"{job_id}_cleaned_{file.filename}")
    tmp_output  = os.path.join(UPLOAD_FOLDER, f"{job_id}_output_{base_name}.dbf")

    try:
        content = await file.read()
        with open(tmp_input, "wb") as f:
            f.write(content)

        validate_dbc_file(tmp_input)

        source_file = tmp_input
        if do_clean:
            clean_dbc_file(tmp_input, tmp_cleaned)
            source_file = tmp_cleaned

        convert_dbc_to_dbf(source_file, tmp_output)

        output_filename = f"{base_name}.dbf"
        return FileResponse(
            path=tmp_output,
            media_type="application/octet-stream",
            filename=output_filename,
            headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    finally:
        for path in [tmp_input, tmp_cleaned]:
            if os.path.exists(path):
                os.remove(path)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Starting DBC→DBF converter at http://localhost:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)