import os
import uuid
import sys
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

sys.path.insert(0, str(Path(__file__).parent))

from validator import validate_dbc_file, ValidationError
from cleaner import clean_dbc_file
from converter import convert_dbc_to_dbf

# Frontend files are at project root
BACKEND_DIR  = Path(__file__).parent
ROOT_DIR     = BACKEND_DIR.parent

app = FastAPI(title="DBC → DBF Converter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve CSS/JS from root
app.mount("/static", StaticFiles(directory=str(ROOT_DIR)), name="static")

UPLOAD_FOLDER = tempfile.gettempdir()
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def check_dbc(filename: str):
    if not filename.lower().endswith(".dbc"):
        raise HTTPException(status_code=400, detail="File must be a .dbc file")


def _cleanup(*paths):
    """Delete temp files after the response has been fully streamed."""
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass  # best-effort cleanup


# ── Frontend ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=(ROOT_DIR / "index.html").read_text(encoding="utf-8"))


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
        # validate endpoint returns JSON — safe to delete synchronously
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Convert ───────────────────────────────────────────────────────────────────

@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    # FIX: default changed to "false" so auto-sanitize is opt-in, not opt-out
    clean: str = Form(default="false"),
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

        # FIX: Use BackgroundTask so temp files are deleted AFTER the response
        # is fully streamed — not before (which caused the 1KB truncation bug).
        return FileResponse(
            path=tmp_output,
            media_type="application/octet-stream",
            filename=output_filename,
            headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
            background=BackgroundTask(_cleanup, tmp_input, tmp_cleaned, tmp_output),
        )

    except ValidationError as e:
        # Clean up synchronously on error — no file is being streamed
        _cleanup(tmp_input, tmp_cleaned, tmp_output)
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    except Exception as e:
        _cleanup(tmp_input, tmp_cleaned, tmp_output)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    print(f"[INFO] Starting DBC→DBF converter at http://localhost:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
