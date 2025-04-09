from fastapi import APIRouter
from app.services.camera_stream import get_current_frame

router = APIRouter()

@router.get("/snapshot", summary="Get latest camera frame")
def snapshot():
    frame_base64 = get_current_frame()
    return {"image": frame_base64}
