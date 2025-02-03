from fastapi import File, UploadFile, HTTPException,APIRouter,Depends
from fastapi.responses import JSONResponse
from app.database import get_db
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
async def analyze_image(task_id: int, file: UploadFile = File(...),db: Session=Depends(get_db)):
    file_path = f"temp_{file.filename}"
    unique_filename = f"inspection_image_{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR_IMG, unique_filename)

        # Save the uploaded image
    with open(file_path, "wb") as out_file:
        out_file.write(await file.read())

    # Analyze the image
    analysis_result =await generate_response_image(file_path, prompt= inspection_bedroom_prompt,media_type="image", task_id=task_id,db=db )

    # Parse the analysis result
    analysis_result = safe_json_loads(analysis_result)
    if not analysis_result:
        raise HTTPException(status_code=500, detail="Failed to analyze the image")

    return JSONResponse(content=analysis_result)
@router.post("/analyze/video/")
async def analyze_video(task_id: int, file: UploadFile = File(...),db: Session=Depends(get_db)):
    #file_path = f"temp_{file.filename}"
    unique_filename = f"inspection_video_{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR_VID, unique_filename)

        # Save the uploaded image
    with open(file_path, "wb") as out_file:
        out_file.write(await file.read())

    # Pass only the file path to generate_response_video
    analysis_result =await generate_response_video(file_path, prompt=inspection_bedroom_prompt,media_type="video", task_id=task_id, db=db)

    # Parse the analysis result
    analysis_result = safe_json_loads(analysis_result)
    if not analysis_result:
        raise HTTPException(status_code=500, detail="Failed to analyze the video")

    return JSONResponse(content=analysis_result)
