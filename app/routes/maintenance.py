from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os

from pydantic import BaseModel
from app.database import get_db

from app.services.analysis_services import process_image, process_image_data_add, process_video, process_maintenance_check, maintenance_check_video

import uuid
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()

UPLOAD_DIR_IMG = "static/uploads/maintenance/images"
UPLOAD_DIR_VID = "static/uploads/maintenance/videos"
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

            
            with open(file_path, "wb") as f:
                f.write(await media_file.read())

           
            result = await process_maintenance_check(file_path=file_path, media_type="image", task_id=task_id, db=db)
            results.append(result)

        return {"results": results}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}, 500

@router.post("/video")
async def analyze_video(task_id: int, media_file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        unique_filename = f"detection_video_{media_file.filename}_{uuid.uuid4()}.mp4"
        file_path = os.path.join(UPLOAD_DIR_VID, unique_filename)
        with open(file_path, "wb") as f:
            f.write(await media_file.read())

        result = await maintenance_check_video(file_path=file_path, media_type="video", task_id=task_id, db=db)
        
        return JSONResponse(content={"result": result})
    except Exception as e:
        db.rollback()
        return JSONResponse(content={"error": str(e)}, status_code=500)




 ###

