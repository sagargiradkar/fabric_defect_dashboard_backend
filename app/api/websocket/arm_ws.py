from fastapi import WebSocket, APIRouter
import asyncio

router = APIRouter()

@router.websocket("/ws/robot-status")
async def robotic_arm_status(websocket: WebSocket):
    await websocket.accept()
    while True:
        await asyncio.sleep(1)
        # Simulated status
        await websocket.send_json({"status": "running"})
