from app.logger import logger

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil

from app.processor import process_excel

# Phase 2
from app.campaign.master import append_new_patients
from app.campaign.scheduler import build_today_list
from app.campaign.followup import process_no_review_file
from app.campaign.sheets import save_master_for_sheet

app = FastAPI()

# --------------------------------------------------
# Base directory (backend/)
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
NO_REVIEW_DIR = BASE_DIR / "data" / "no_review"

STATIC_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
NO_REVIEW_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Serve frontend
# --------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def frontend():
    return (STATIC_DIR / "index.html").read_text()


# --------------------------------------------------
# Upload daily patient Excel
# --------------------------------------------------
@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        logger.info(f"File received: {file.filename}")

        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # -------- Phase 1: Clean Excel --------
        clean_df = process_excel(str(file_path))
        logger.info(f"Clean dataframe rows: {len(clean_df)}")

        # -------- Phase 2: Master + Scheduler --------
        master = append_new_patients(clean_df)

        today_df, updated_master = build_today_list(master)

        # Save updated master for Google Sheet paste
        save_master_for_sheet(updated_master)

        logger.info(f"Today's send list size: {len(today_df)}")

        # -------- Create doctor-wise CSV from TODAY list --------
        doctors_dir = OUTPUT_DIR / "doctors"
        doctors_dir.mkdir(exist_ok=True)

        for doctor, group in today_df.groupby("Appointment Provider Name"):
            doctor_file = doctors_dir / f"{doctor.replace(' ', '_')}.csv"
            group[["Patient First Name", "Patient Email"]].to_csv(
                doctor_file, index=False
            )

        combined_path = OUTPUT_DIR / "today_send.csv"
        today_df.to_csv(combined_path, index=False)

        # -------- Zip --------
        zip_base = OUTPUT_DIR / "doctor_email_files"
        shutil.make_archive(str(zip_base), "zip", OUTPUT_DIR)

        zip_path = str(zip_base) + ".zip"

        logger.info("ZIP created and returning to frontend")

        return FileResponse(zip_path, filename="doctor_email_files.zip")

    except Exception:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Upload failed")


# --------------------------------------------------
# Upload NO REVIEW file
# --------------------------------------------------
@app.post("/upload-no-review")
async def upload_no_review(file: UploadFile = File(...)):
    try:
        path = NO_REVIEW_DIR / "latest_no_review.csv"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        process_no_review_file(str(path))

        return {"message": "No review file processed successfully"}

    except Exception:
        logger.exception("No review upload failed")
        raise HTTPException(status_code=500, detail="No review processing failed")
