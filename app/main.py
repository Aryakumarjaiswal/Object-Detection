from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
#from app.models.models import MediaUpload, DetectionResults, DetectedObjects 
from app.routes import detection_router, add_elementry_router, maintenance_router,inspection_router
Base.metadata.create_all(bind=engine)


app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = FastAPI.openapi(app)  
    openapi_schema["info"]["title"] = "Object Detection"
    openapi_schema["info"]["version"] = "1.1.0"
    openapi_schema["info"]["description"] = "This API serves as the backend for Object Detection."
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(detection_router, prefix="/detection")
app.include_router(add_elementry_router,  prefix="/api", tags=["Add Elementary Data"])
app.include_router(maintenance_router,  prefix="/api", tags=["Maintainance"])
app.include_router(inspection_router,prefix="/api",tags=['Inspection'])
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8003, reload=True, host="0.0.0.0")
