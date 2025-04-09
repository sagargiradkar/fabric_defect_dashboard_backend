# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    CAMERA_INDEX: int = 0
    YOLO_MODEL_PATH: str = "weights/yolov11.pt"
    DB_URL: str = "sqlite:///./fabric_inspection.db"
    LOG_LEVEL: str = "info"
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000"]
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
