import json
from google.generativeai import GenerativeModel, upload_file, get_file, delete_file
import google.generativeai as genai
# from app.services.database import (insert_media,insert_detection_results, insert_detected_objects,)
from PIL import Image
import tempfile
import os

from sqlalchemy import func
from app.models.models import Inventory, Inventory_Compersion,InspectionCheck
from app.services.prompt_generator import general_prompt, general_video_prompt, maintenance_prompt
import time
from app.services.get_task import fetch_task_by_id
from fastapi import HTTPException
from app.services.draw_bounding_boxes import draw_bounding_boxes
import uuid
from dotenv import load_dotenv
from ..models import MediaUpload,MaintenanceCheck, DetectionResults, DetectedObjects,InspectionCheck
from ..database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException,Depends
from ..database import get_db, SessionLocal
import logging

load_dotenv() 


GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

GENERATION_CONFIG = {
    "temperature": 0,
    "top_p": 0.8,
    "top_k": 128,
    "max_output_tokens": 4096,
    "response_mime_type": "application/json",
    
}

UPLOAD_DIR_BOUNDING_BOX_IMG = "static/uploads/bounding_box_images/"
os.makedirs(UPLOAD_DIR_BOUNDING_BOX_IMG, exist_ok=True)

BASE_URL_PATH =  os.getenv("BASE_URL_PATH1")
print(f"BASE_URL_PATH: {BASE_URL_PATH}")
################################################### IMAGE PROCESSING ###################################################

async def process_image(file_path, media_type, task_id, db: Session):
    try:
        # Fetch task data
        task_data = await fetch_task_by_id(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Extract task details
    task_type = task_data["task_type"]
    unit_id = task_data["unit_id"]
    property_id = task_data["property_id"]

    # Save media upload record to the database
    upload_db = MediaUpload(
        task_type=task_type,
        unit_id=unit_id,
        property_id=property_id,
        media_type=media_type,
        media_url=file_path,
    )
    db.add(upload_db)
    db.flush()
    db.refresh(upload_db)
    upload_id_value = upload_db.upload_id  # Get the uploaded ID for later use

    # Open and process the image
    with open(file_path, "rb") as image_file:
        image = Image.open(image_file)
        model = GenerativeModel(
            model_name="models/gemini-1.5-pro", generation_config=GENERATION_CONFIG
        )
        response = model.generate_content([general_prompt, image])

    # Parse response
    response_json = json.loads(response.text)

    # Initialize a dictionary to hold detected items
    detected_items = {}

    # Process each object in the detected objects list
    for obj in response_json["objects"]:
        if isinstance(obj, dict):  # Ensure it's a dictionary
            label = obj.get("label", "Unknown")
            bounding_box = obj.get("bounding_box", {})
            detected_items[label] = detected_items.get(label, 0) + 1
        else:
            print("Invalid object structure:", obj)  # Log if object is not a dictionary

    # Draw bounding boxes on the image and save it
    image_with_bounding_boxes = draw_bounding_boxes(
        file_path=file_path, bounding_boxes=response_json["objects"]
    )
    unique_filename = f"bounding_box_{uuid.uuid4()}.png"
    save_path_bounding_box_img = os.path.join(UPLOAD_DIR_BOUNDING_BOX_IMG, unique_filename)
    image_with_bounding_boxes.save(save_path_bounding_box_img)

    # Create detection results in the database
    result_db = DetectionResults(
        upload_id=upload_id_value,
        detected_items=detected_items,
        detected_count=len(response_json["objects"]),
        bounding_box_summary=response_json,
        image_with_bounding_box_url=save_path_bounding_box_img,
    )
    db.add(result_db)
    db.flush()
    db.refresh(result_db)

    # Insert each detected object as a separate entry in DetectedObjects table
    all_data = []
    for obj in response_json["objects"]:
        bounding_box = obj.get("bounding_box", [])
        if len(bounding_box) == 4:  # Check if bounding box is valid
            ymin, xmin, ymax, xmax = bounding_box
        else:
            ymin = xmin = ymax = xmax = 0  # Default values if bounding box is missing or malformed

        detect_db = DetectedObjects(
            result_id=result_db.result_id,
            label=obj.get("label", "Unknown"),
            ymin=ymin,
            xmin=xmin,
            ymax=ymax,
            xmax=xmax,
        )
        all_data.append(detect_db)

    # Fetch the inventory data based on task_id
    element_data = db.query(Inventory).filter(Inventory.task_id == task_id).first()

    # Add all detected objects to the database
    db.add_all(all_data)
    db.commit()

    # Optionally, compare the detected items with existing inventory and add the result to the Inventory_Compersion table
    comparison_data = Inventory_Compersion(
        result_id=result_db.result_id,
        task_id=task_id,
        task_type=task_type,
        unit_id=unit_id,
        property_id=property_id,
        existing_item=element_data.existing_item if element_data else {},
        existing_count=element_data.existing_count if element_data else 0,
        detected_item=detected_items,
        detected_count=len(response_json["objects"]),
    )
    db.add(comparison_data)
    db.commit()

    # Return a response with detected count and other useful information
    return {
        
        "detected_count": len(response_json["objects"]),
        "detected_items": detected_items,
        "image_path": f"{BASE_URL_PATH}/{save_path_bounding_box_img}" if save_path_bounding_box_img else None,
        "response_json": response_json  # Return the full response for debugging purposes
    }

######################################################### process_video ############################################

async def process_video(file_path, media_type, task_id,  db:Session=Depends(get_db)):

    try:
        task_data = await fetch_task_by_id(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    task_type = task_data["task_type"]
    unit_id = task_data["unit_id"]
    property_id = task_data["property_id"]

    upload_db = MediaUpload(
        task_type=task_type,
        unit_id=unit_id,
        property_id=property_id,
        media_type=media_type,
        media_url=file_path,
    )
    db.add(upload_db)
    db.commit()
    db.refresh(upload_db)
    
    video_upload = upload_file(path=file_path, mime_type="video/mp4")
    while video_upload.state.name == "PROCESSING":
        time.sleep(10)
        video_upload = get_file(video_upload.name)

    if video_upload.state.name == "FAILED":
        raise Exception("Video processing failed.")

    model = GenerativeModel(
        model_name="models/gemini-1.5-pro", generation_config=GENERATION_CONFIG
    )
    response = model.generate_content([general_video_prompt, video_upload])
    delete_file(video_upload.name)

    response_json = json.loads(response.text)

    result_db = DetectionResults(
        upload_id=upload_db.upload_id,
        detected_items=response_json["visible_objects"],
        detected_count=sum(response_json["visible_objects"].values()),
        bounding_box_summary=response_json,
    )
    db.add(result_db)
    db.commit()
    db.refresh(result_db)

    return {
        "videos_path": f"{BASE_URL_PATH}/{os.path.normpath(file_path).replace(os.sep, '/')}",
        "detected_count": result_db.detected_count,
        "response_json": response_json,
         
    }



################################################## for add data  in Inventry Table ######################################################


async def process_image_data_add(file_path, media_type, task_id, db: Session):
    try:
        # Fetch the task data using the provided task ID
        task_data = await fetch_task_by_id(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Extract task details for inventory record
    task_type = task_data["task_type"]
    unit_id = task_data["unit_id"]
    property_id = task_data["property_id"]

    # Open the image and process it with the generative model
    with open(file_path, "rb") as image_file:
        image = Image.open(image_file)
        model = GenerativeModel(
            model_name="models/gemini-1.5-pro", generation_config=GENERATION_CONFIG
        )
        response = model.generate_content([general_prompt, image])

    # Handle the response from the model
    try:
        # Check if response is a dictionary-like object
        if hasattr(response, "to_dict"):
            response_json = response.to_dict()
        elif hasattr(response, "text"):
            response_json = json.loads(response.text)
        else:
            raise HTTPException(
                status_code=500,
                detail="Error processing images: Unsupported response structure."
            )

        # Navigate to the required content
        content_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        parsed_content = json.loads(content_text)  # Parse JSON string
    except (AttributeError, KeyError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Error processing response: {e}")

    # Parse detected objects
    detected_items = []
    for obj in parsed_content.get("objects", []):
        if isinstance(obj, dict):
            label = obj.get("label", "Unknown")
            bounding_box = obj.get("bounding_box", {})
            detected_items.append({
                "label": label,
                "bounding_box": bounding_box,
                "count": 1
            })
        else:
            print("Invalid object structure:", obj)

    # Generate summary
    general_description = parsed_content.get("general_description", "No description available")
    summary = {
        "total_objects": len(parsed_content.get("objects", [])),
        "object_labels": list(set([obj["label"] for obj in parsed_content.get("objects", [])])),
    }

    # Draw bounding boxes on the image and save the resulting image
    image_with_bounding_boxes = draw_bounding_boxes(
        file_path=file_path, bounding_boxes=parsed_content.get("objects", [])
    )

    # Generate a unique filename for the image with bounding boxes
    unique_filename = f"bounding_box_{uuid.uuid4()}.png"
    save_path_bounding_box_img = os.path.join(UPLOAD_DIR_BOUNDING_BOX_IMG, unique_filename)
    image_with_bounding_boxes.save(save_path_bounding_box_img)

    # Create an inventory record with the detected items and counts
    result_db = Inventory(
        task_id=task_id,
        task_type=task_type,
        unit_id=unit_id,
        property_id=property_id,
        existing_item=detected_items,  # Store all detected items in the database
        existing_count=len(parsed_content.get("objects", [])),  # Total count of detected objects
        summary=summary,  # Include the summary
        general_description=general_description
    )

    # Add the result to the database and commit
    db.add(result_db)
    db.commit()
    db.refresh(result_db)

    # Return the detected count, summary, and full response for debugging
    return {
        "inventory_id":result_db.inventory_id,
        "detected_count": len(parsed_content.get("objects", [])),
        "summary": summary,
        "response_json": parsed_content,
        #"general_description": general_description
    }

######################## for Maintenance ###########################


async def process_maintenance_check(file_path, media_type, task_id, db: Session):
    try:
        # Fetch task data
        task_data = await fetch_task_by_id(task_id)

        # Extract task details
        task_type = task_data["task_type"]
        unit_id = task_data["unit_id"]
        property_id = task_data["property_id"]

        # Save media upload record to the database
        upload_db = MediaUpload(
            task_type=task_type,
            unit_id=unit_id,
            property_id=property_id,
            media_type=media_type,
            media_url=file_path,
        )
        db.add(upload_db)
        db.flush()
        db.refresh(upload_db)
        upload_id_value = upload_db.upload_id  # Get the uploaded ID for later use

        # Open and process the image
        with open(file_path, "rb") as image_file:
            image = Image.open(image_file)
            model = GenerativeModel(
                model_name="models/gemini-1.5-pro", generation_config=GENERATION_CONFIG
            )
            response = model.generate_content([maintenance_prompt, image])

        # Parse response
        response_json = json.loads(response.text)
        status_val=""
   
        
        for key in response_json:
                
                if key=="general_description":
                    break
                status_val+=f"{key} -> {response_json[key]},    "
               
        #print(status_val)
        
        maintenance_check = MaintenanceCheck(
            upload_id=upload_db.upload_id,
            status=status_val,
            general_description=response_json["general_description"]
        )
        
        db.add(maintenance_check)
        db.commit()
        db.refresh(maintenance_check)
        bounding_img=await process_image(file_path=file_path, media_type="image", task_id=task_id, db=db)
        fin_response_json={"Status":status_val,"general_description":response_json["general_description"],"image_path":f"{BASE_URL_PATH}/{os.path.normpath(file_path).replace(os.sep, '/')}",}
        return fin_response_json
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}") from e
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail="Failed to parse response JSON") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
async def maintenance_check_video(file_path, media_type, task_id,  db:Session=Depends(get_db)):

    try:
        task_data = await fetch_task_by_id(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:

        task_type = task_data["task_type"]
        unit_id = task_data["unit_id"]
        property_id = task_data["property_id"]

        upload_db = MediaUpload(
        task_type=task_type,
        unit_id=unit_id,
        property_id=property_id,
        media_type=media_type,
        media_url=file_path,
    )
        db.add(upload_db)
        db.commit()
        db.refresh(upload_db)
    
        video_upload = upload_file(path=file_path, mime_type="video/mp4")
        while video_upload.state.name == "PROCESSING":
            time.sleep(10)
            video_upload = get_file(video_upload.name)

        if video_upload.state.name == "FAILED":
            raise Exception("Video processing failed.")

        model = GenerativeModel(
            model_name="models/gemini-1.5-pro", generation_config=GENERATION_CONFIG
    )
        response = model.generate_content([maintenance_prompt, video_upload])
        delete_file(video_upload.name)

        response_json = json.loads(response.text)
        print(response_json)
       
        
        status_val=""
        for key in response_json:
                
                if key=="general_description":
                    break
                status_val+=f"{key} -> {response_json[key]},    "
       
        maintenance_check = MaintenanceCheck(
            upload_id=upload_db.upload_id,
            status=status_val,
            general_description=response_json["general_description"]
        )
        
        db.add(maintenance_check)
        db.commit()
        db.refresh(maintenance_check)
        fin_response_json={"Status":status_val,"general_description":response_json["general_description"]}
        return {
            "video_path": f"{BASE_URL_PATH}/{os.path.normpath(file_path).replace(os.sep, '/')}",
            "maintenance_results": fin_response_json,
            "upload_id": upload_db.upload_id,
            "maintenance_check_id": maintenance_check.id
        }

    except Exception as e:

        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing maintenance check: {str(e)}"
        )


            ######################## for Inspection ###########################
async def generate_response_image(image_file, prompt, media_type, task_id, db:Session=Depends(get_db)):
    # Define the prompt for Gemini model
    try:
        task_data = await fetch_task_by_id(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:

        task_type = task_data["task_type"]
        unit_id = task_data["unit_id"]
        property_id = task_data["property_id"]

        upload_db = MediaUpload(
        task_type=task_type,
        unit_id=unit_id,
        property_id=property_id,
        media_type=media_type,
        media_url=image_file,
    )
        db.add(upload_db)
        db.commit()
        db.refresh(upload_db)
        
    
        # Open the image and convert to binary
        
        image = Image.open(image_file)
        # Define the model with configuration
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-pro", generation_config=GENERATION_CONFIG
        )
        response = model.generate_content([prompt, image])
        response_json = json.loads(response.text)
        inspection_check = InspectionCheck(
            upload_id=upload_db.upload_id,
            status=f"Rating: {response_json["ai_rating"]}, Condition: {response_json["condition"]}",
            general_description=response_json["description"]
        )
        
        db.add(inspection_check)
        db.commit()
        db.refresh(inspection_check)
        
        print(type(response_json))
        print(response_json)
        response_json['image_path']=f"{BASE_URL_PATH}/{os.path.normpath(image_file).replace(os.sep, '/')}"#"image_file":image_file
        return response_json

    except Exception as e:
        return {"error": f"Error in generating response from Gemini: {str(e)}"}

async def generate_response_video(video_file_path: str, prompt: str, media_type, task_id,  db:Session=Depends(get_db)):
    try:
        task_data = await fetch_task_by_id(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        task_type = task_data["task_type"]
        unit_id = task_data["unit_id"]
        property_id = task_data["property_id"]

        upload_db = MediaUpload(
        task_type=task_type,
        unit_id=unit_id,
        property_id=property_id,
        media_type=media_type,
        media_url=video_file_path,
    )
        db.add(upload_db)
        db.commit()
        db.refresh(upload_db)
        file_extension = os.path.splitext(video_file_path)[1].lower()

        
        if file_extension == ".mp4":
            mime_type = "video/mp4"
            suffix = ".mp4"
        elif file_extension == ".mov":
            mime_type = "video/quicktime"
            suffix = ".mov"
        else:
            raise ValueError("Unsupported video format. Only .mp4 and .mov are allowed.")

        # Create a temporary file and copy video content
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_video:
            with open(video_file_path, "rb") as original_video:
                temp_video.write(original_video.read())  # Read and copy file content
            
            temp_video.flush()
            temp_video_path = temp_video.name

        # Upload the video
        video_upload = genai.upload_file(path=temp_video_path, mime_type=mime_type)

        # Polling to check status of video processing
        while video_upload.state.name == "PROCESSING":
            time.sleep(10)
            video_upload = genai.get_file(video_upload.name)

        if video_upload.state.name == "FAILED":
            raise ValueError("Video processing failed.")

        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-pro", generation_config=GENERATION_CONFIG
        )
        response = model.generate_content(
            [prompt, video_upload], request_options={"timeout": 600}
        )
        print(response)
        response_json = json.loads(response.text)
        inspection_check = InspectionCheck(
            upload_id=upload_db.upload_id,
            status=f"Rating: {response_json["ai_rating"]}, Condition: {response_json["condition"]}",
            general_description=response_json["description"]
        )
        
        db.add(inspection_check)
        db.commit()
        db.refresh(inspection_check)
        response_json['video_path']=f"{BASE_URL_PATH}/{os.path.normpath(video_file_path).replace(os.sep, '/')}"
        # Cleanup
        genai.delete_file(video_upload.name)
        os.remove(temp_video_path)
        #os.remove(video_file_path)  # Delete the uploaded video after processing
        
        return response_json

    except Exception as e:
        return {"error": f"Error in generating response from Gemini: {str(e)}"}


