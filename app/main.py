from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import camera, metrics, robotic_arm
from app.api.websocket import camera_ws, arm_ws
from app.core.config import settings  # <-- import the settings

app = FastAPI()

# Use CORS origins from .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # From .env via pydantic
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register HTTP routes
app.include_router(camera.router, prefix="/api/camera")
app.include_router(metrics.router, prefix="/api/metrics")
app.include_router(robotic_arm.router, prefix="/api/robotic_arm")

# Register WebSocket routes
app.include_router(camera_ws.router)
app.include_router(arm_ws.router)
