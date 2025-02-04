  
from sqlalchemy import DateTime,Column, Integer, String, Float, Enum, JSON, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class MediaUpload(Base):
    __tablename__ = "media_upload"

    upload_id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(255), nullable=False)
    unit_id = Column(Integer, nullable=False)
    property_id = Column(Integer, nullable=False)
    media_type = Column(Enum("image", "video", name="media_type"), nullable=False)
    media_url = Column(String(500), nullable=False)
    uploaded_at = Column(TIMESTAMP, default=func.now())

    detection_results = relationship("DetectionResults", back_populates="media_upload", cascade="all, delete")
    maintenance_checks = relationship("MaintenanceCheck", back_populates="media_upload", cascade="all, delete")
    inspection_checks=relationship("InspectionCheck",back_populates="media_upload", cascade="all, delete")

class DetectionResults(Base):
    __tablename__ = "detection_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer,ForeignKey("media_upload.upload_id", ondelete="CASCADE"),nullable=False)
    detected_items = Column(JSON, nullable=False)
    detected_count = Column(Integer, nullable=False)
    bounding_box_summary = Column(JSON, nullable=True)
    image_with_bounding_box_url = Column(String(500), nullable=True)
    detected_at = Column(TIMESTAMP, default=func.now())

    media_upload = relationship("MediaUpload", back_populates="detection_results")
    detected_objects = relationship("DetectedObjects", back_populates="detection_results", cascade="all, delete")
    Inventory_Compersions = relationship("Inventory_Compersion", back_populates="detection_results")


class DetectedObjects(Base):
    __tablename__ = "detected_objects"

    object_id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("detection_results.result_id", ondelete="CASCADE"),nullable=False)
    label = Column(String(255), nullable=False)
    ymin = Column(Float, nullable=False)
    xmin = Column(Float, nullable=False)
    ymax = Column(Float, nullable=False)
    xmax = Column(Float, nullable=False)

    detection_results = relationship("DetectionResults", back_populates="detected_objects")

class Inventory(Base):
    __tablename__ = "inventory_tb2"

    inventory_id  = Column(Integer, primary_key=True, autoincrement=True)
    task_id =Column(Integer, nullable=False)
    task_type = Column(String(255), nullable=False)
    unit_id = Column(Integer, nullable=False)
    property_id = Column(Integer, nullable=False)
    existing_item=Column(JSON, nullable=False)
    existing_count=Column(Integer, nullable=False)
    summary = Column(JSON, nullable=True)
    general_description=Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())

class Inventory_Compersion(Base):
    __tablename__ = "Inventory_Compersion"

    inventory_id  = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("detection_results.result_id", ondelete="CASCADE"),nullable=False)
    task_id =Column(Integer, nullable=False)
    task_type = Column(String(255), nullable=False)
    unit_id = Column(Integer, nullable=False)
    property_id = Column(Integer, nullable=False)
    existing_item=Column(JSON, nullable=False)
    existing_count=Column(Integer, nullable=False)
    detected_item=Column(JSON, nullable=False)
    detected_count=Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())

    detection_results = relationship("DetectionResults", back_populates="Inventory_Compersions")
    

class MaintenanceCheck(Base):
    __tablename__ = "maintenance_checks"

    id = Column(Integer, primary_key=True, index=True)
    
    upload_id = Column(Integer, ForeignKey("media_upload.upload_id"))
    status =  Column(Text)
    general_description = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())
    
    media_upload = relationship("MediaUpload", back_populates="maintenance_checks")   

class InspectionCheck(Base):
    __tablename__ = "inspection_checks"

    id = Column(Integer, primary_key=True, index=True)
    
    upload_id = Column(Integer, ForeignKey("media_upload.upload_id"))
    status = Column(Text)
    general_description = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())

    media_upload = relationship("MediaUpload", back_populates="inspection_checks")   
