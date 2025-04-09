from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DefectLog(Base):
    __tablename__ = 'defect_logs'
    id = Column(Integer, primary_key=True, index=True)
    defect_type = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class RoboticArmStatus(Base):
    __tablename__ = 'robotic_arm_status'
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
