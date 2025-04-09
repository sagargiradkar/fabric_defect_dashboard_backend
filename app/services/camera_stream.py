import cv2
import base64
from fastapi import WebSocket
from app.core.config import settings

class CameraStream:
    def __init__(self, camera_index=settings.CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)

    async def start_stream(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    continue  # Skip this iteration if frame is not captured

                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = base64.b64encode(buffer).decode('utf-8')

                await websocket.send_json({
                    "type": "camera_feed",
                    "payload": {
                        "image": frame_bytes
                    }
                })
        except Exception as e:
            print(f"Camera stream error: {e}")
        finally:
            self.cap.release()
            await websocket.close()
