from fastapi import APIRouter
from app.services.robotic_arm import start_arm, stop_arm, reset_arm

router = APIRouter()

@router.post("/start", summary="Start robotic arm sorting")
def start():
    return start_arm()

@router.post("/stop", summary="Stop robotic arm")
def stop():
    return stop_arm()

@router.post("/reset", summary="Reset robotic arm position")
def reset():
    return reset_arm()
