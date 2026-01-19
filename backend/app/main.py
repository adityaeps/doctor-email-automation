from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil

from app.processor import process_excel
from app.utils import logger

app = FastAPI()

# --------------------------------------------------
# Base directory (backend/)
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Serve frontend
# --------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def frontend():
    return (STATIC_DIR / "index.html").read_text()


# --------------------------------------------------
# Upload endpoint
# --------------------------------------------------
@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        logger.info(f"File received: {file.filename}")

        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        zip_path = process_excel(str(file_path), str(OUTPUT_DIR))

        return FileResponse(
            zip_path,
            filename="doctor_email_files.zip"
        )

    except Exception:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Upload failed")
