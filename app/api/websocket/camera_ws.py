from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Your image frame sending logic here
            await websocket.send_text("WebSocket connected!")
    except WebSocketDisconnect:
        print("Client disconnected")
