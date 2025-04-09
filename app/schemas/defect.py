from pydantic import BaseModel
from datetime import datetime

class DefectBase(BaseModel):
    defect_type: str

class DefectCreate(DefectBase):
    pass

class Defect(DefectBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
