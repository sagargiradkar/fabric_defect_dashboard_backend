from sqlalchemy.orm import Session
from app.db import models
from app.schemas import defect as defect_schema, robot as robot_schema

def create_defect_log(db: Session, defect: defect_schema.DefectCreate):
    db_defect = models.DefectLog(**defect.dict())
    db.add(db_defect)
    db.commit()
    db.refresh(db_defect)
    return db_defect

def get_defect_logs(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.DefectLog).offset(skip).limit(limit).all()

def create_robotic_arm_status(db: Session, status: robot_schema.RoboticArmStatusCreate):
    db_status = models.RoboticArmStatus(**status.dict())
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_robotic_arm_status(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.RoboticArmStatus).offset(skip).limit(limit).all()
