from pydantic import BaseModel
from datetime import datetime

class RoboticArmStatusBase(BaseModel):
    status: str

class RoboticArmStatusCreate(RoboticArmStatusBase):
    pass

class RoboticArmStatus(RoboticArmStatusBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
