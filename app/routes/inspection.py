

from fastapi import File, UploadFile, HTTPException,APIRouter,Depends
from fastapi.responses import JSONResponse
from app.database import get_db
from typing import List
from sqlalchemy.orm import Session
from app.services.analysis_services import generate_response_image,generate_response_video
from app.services.prompt_generator import inspection_bedroom_prompt
import json
import uuid
import os
router =APIRouter()
UPLOAD_DIR_IMG = "static/uploads/inspection/images"
UPLOAD_DIR_VID = "static/uploads/inspection/videos"
os.makedirs(UPLOAD_DIR_IMG, exist_ok=True)
os.makedirs(UPLOAD_DIR_VID, exist_ok=True)

# Function to safely parse JSON
def safe_json_loads(response_text):
    if isinstance(response_text, dict):
        return response_text
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON response")



@router.post("/analyze/image/")
async def analyze_image(
    task_id: int, 
    files: List[UploadFile] = File(...),  
    db: Session = Depends(get_db)
):
    file_paths = []
    results = []

    for file in files:
        unique_filename = f"inspection_image_{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR_IMG, unique_filename)

        # Save the uploaded image
        with open(file_path, "wb") as out_file:
            out_file.write(await file.read())

        file_paths.append(file_path)

    if not file_paths:
        raise HTTPException(status_code=400, detail="No files were uploaded")

    # Process each image separately
    for file_path in file_paths:
        analysis_result = await generate_response_image(
            file_path, 
            prompt=inspection_bedroom_prompt, 
            media_type="image", 
            task_id=task_id, 
            db=db
        )

        # Parse the analysis result
        analysis_result = safe_json_loads(analysis_result)
        if not analysis_result:
            return "Couldnt process analysis result"  

        results.append(analysis_result)

    if not results:
        raise HTTPException(status_code=500, detail="Failed to analyze images")

    return JSONResponse(content={"results": results})


@router.post("/analyze/video/")
async def analyze_video(
    task_id: int, 
    files: List[UploadFile] = File(...),  # Allow multiple video uploads
    db: Session = Depends(get_db)
):
    file_paths = []
    results = []

    for file in files:
        unique_filename = f"inspection_video_{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR_VID, unique_filename)

        # Save the uploaded video
        with open(file_path, "wb") as out_file:
            out_file.write(await file.read())

        file_paths.append(file_path)

    if not file_paths:
        raise HTTPException(status_code=400, detail="No files were uploaded")

    # Process each video separately
    for file_path in file_paths:
        analysis_result = await generate_response_video(
            file_path, 
            prompt=inspection_bedroom_prompt, 
            media_type="video", 
            task_id=task_id, 
            db=db
        )

        # Parse the analysis result
        analysis_result = safe_json_loads(analysis_result)
        if not analysis_result:
            return "Couldnt process analysis result"

        results.append(analysis_result)

    if not results:
        raise HTTPException(status_code=500, detail="Failed to analyze videos")

    return JSONResponse(content={"results": results})
