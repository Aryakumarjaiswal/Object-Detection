from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os

from pydantic import BaseModel
from app.database import get_db
from app.models.models import Inventory
from app.services.analysis_services import process_image, process_image_data_add, process_video
# from app.services.database import rollback_transaction, commit_transaction
import uuid
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()

UPLOAD_DIR_IMG = "static/uploads/images"
UPLOAD_DIR_VID = "static/uploads/videos"
os.makedirs(UPLOAD_DIR_IMG, exist_ok=True)
os.makedirs(UPLOAD_DIR_VID, exist_ok=True)

################################################### for add Inventery Data api ############################################

class InventoryUpdate(BaseModel):
    task_type: str
    unit_id: int
    property_id: int
    existing_item: dict
    existing_count: int
    summary: dict
    general_description: str

@router.post("/images/add_data")
async def analyze_images_add_data(
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
            result = await process_image_data_add(file_path=file_path, media_type="image", task_id=task_id, db=db)
            results.append(result)

        return {"results": results}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing images: {str(e)}")
    


@router.get("/images/inventory/{inventory_id}", response_model=None)
async def get_inventory_by_task_id(inventory_id: int, db: Session = Depends(get_db)):
    try:
        # Query to get inventory based on task_id
        inventory_records = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
        if not inventory_records:
            raise HTTPException(status_code=404, detail="Inventory not found")
        return inventory_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inventory: {str(e)}")


@router.get("/images/inventory", response_model=None)
async def get_all_inventory(db: Session = Depends(get_db)):
    try:
        # Query to get all inventory records
        inventory_records = db.query(Inventory).all()
        if not inventory_records:
            raise HTTPException(status_code=404, detail="No inventory records found")
        return inventory_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inventory: {str(e)}")

@router.put("/images/inventory/{inventory_id}")
async def update_inventory(
    inventory_id: int,
    inventory_update: InventoryUpdate,
    db: Session = Depends(get_db)
):
    try:
        # Fetch the inventory record by inventory_id
        inventory_record = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()

        if not inventory_record:
            raise HTTPException(status_code=404, detail="Inventory not found")

        # Update the fields with new data
        inventory_record.task_type = inventory_update.task_type
        inventory_record.unit_id = inventory_update.unit_id
        inventory_record.property_id = inventory_update.property_id
        inventory_record.existing_item = inventory_update.existing_item
        inventory_record.existing_count = inventory_update.existing_count
        inventory_record.summary = inventory_update.summary
        inventory_record.general_description = inventory_update.general_description

        db.commit()  # Commit the changes to the database
        db.refresh(inventory_record)  # Refresh to get updated record

        return {"detail": "Inventory record updated successfully", "inventory": inventory_record}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating inventory: {str(e)}")


@router.delete("/images/inventory/{inventory_id}")
async def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    try:
        # Fetch the inventory record by inventory_id
        inventory_record = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()

        if not inventory_record:
            raise HTTPException(status_code=404, detail="Inventory not found")

        # Delete the inventory record
        db.delete(inventory_record)
        db.commit()

        return {"detail": "Inventory record deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting inventory: {str(e)}")
