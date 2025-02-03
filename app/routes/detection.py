from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os

from app.database import get_db
from app.models.models import Inventory
from app.services.analysis_services import process_image, process_image_data_add, process_video, process_maintenance_check
# from app.services.database import rollback_transaction, commit_transaction
import uuid
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()

UPLOAD_DIR_IMG = "static/uploads/images"
UPLOAD_DIR_VID = "static/uploads/videos"
os.makedirs(UPLOAD_DIR_IMG, exist_ok=True)
os.makedirs(UPLOAD_DIR_VID, exist_ok=True)


@router.post("/images")
async def analyze_images(
    task_id: int, 
    media_files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db)
):
    try:
        results = []
        for media_file in media_files:
            unique_filename = f"detection_image_{uuid.uuid4()}_{media_file.filename}"
            file_path = os.path.join(UPLOAD_DIR_IMG, unique_filename)

            # Save uploaded file to disk
            with open(file_path, "wb") as f:
                f.write(await media_file.read())

            # Process image and store results
            result = await process_image(file_path=file_path, media_type="image", task_id=task_id, db=db)
            results.append(result)
            print(result)

        return {"results": results}

    except Exception as e:
        db.rollback()
        return {"error occured": str(e)}, 500


@router.post("/video")
async def analyze_video(task_id: int, media_file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        unique_filename = f"detection_video_{media_file.filename}_{uuid.uuid4()}.mp4"
        file_path = os.path.join(UPLOAD_DIR_VID, unique_filename)
        with open(file_path, "wb") as f:
            f.write(await media_file.read())

        result = await process_video(file_path=file_path, media_type="video", task_id=task_id, db=db)

        return JSONResponse(content={"result": result})
    except Exception as e:
        db.rollback()
        return JSONResponse(content={"error": str(e)}, status_code=500)

