# config/settings.py
"""
Configuration settings for the Fabric Defect Detection System.

This module contains all the configurable settings for the application,
including paths, model settings, camera settings, and robot arm parameters.
Settings can be overridden through environment variables.
"""

import torch
import os
import logging
from pathlib import Path


class Settings:
    """Application configuration settings"""

    # Basic app info
    PROJECT_NAME = "Live Fabric Defect Detector with Robot Arm"
    VERSION = "1.0.0"

    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    MODEL_PATH = os.environ.get("FABRIC_MODEL_PATH", "/home/sagar/new_model/best.pt")
    LOG_FILE = os.environ.get(
        "FABRIC_LOG_FILE", str(BASE_DIR / "logs" / "fabric_robot.log")
    )

    # Model settings
    CLASS_NAMES = ["Hole", "Stitch", "Seam"]
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    DETECTION_THRESHOLD = float(os.environ.get("FABRIC_DETECTION_THRESHOLD", "0.6"))

    # Camera settings
    CAMERA_WIDTH = int(os.environ.get("FABRIC_CAMERA_WIDTH", "640"))
    CAMERA_HEIGHT = int(os.environ.get("FABRIC_CAMERA_HEIGHT", "480"))
    FRAME_RATE = int(
        os.environ.get("FABRIC_FRAME_RATE", "1")
    )  # Low frame rate to reduce lag

    # UI settings
    WINDOW_SIZE = os.environ.get("FABRIC_WINDOW_SIZE", "1080x720")

    # Robot arm settings
    GRIPPER_CHANNEL = int(os.environ.get("FABRIC_GRIPPER_CHANNEL", "3"))
    DETECTION_COOLDOWN = int(os.environ.get("FABRIC_DETECTION_COOLDOWN", "5"))

    # Movement speed settings
    MOVEMENT_STEPS = int(os.environ.get("FABRIC_MOVEMENT_STEPS", "50"))
    MOVEMENT_DELAY = float(os.environ.get("FABRIC_MOVEMENT_DELAY", "0.01"))

    # Robot arm positions - these could also be loaded from a JSON file for easier configuration
    ARM_POSITIONS = {
        "home": {0: 120, 1: 45, 2: 45},
        "pickup": {0: 0, 1: 0, 2: 180},
        "defective": {0: 180, 1: 0, 2: 180},
        "non_defective": {0: 90, 1: 0, 2: 180},
    }

    @staticmethod
    def check_cuda():
        """Check and log CUDA availability"""
        logger = logging.getLogger("fabric_detection.settings")
        logger.info(f"Using device: {Settings.DEVICE}")
        if torch.cuda.is_available():
            logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
            # Log CUDA memory info
            logger.info(
                f"CUDA memory allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB"
            )
            logger.info(
                f"CUDA memory cached: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB"
            )
        else:
            logger.warning("CUDA not available. Using CPU.")

    @staticmethod
    def load_custom_positions(file_path=None):
        """
        Load custom arm positions from a configuration file

        Args:
            file_path: Path to the JSON configuration file

        Returns:
            Dictionary of positions or None if file doesn't exist
        """
        if file_path is None:
            file_path = os.environ.get(
                "FABRIC_POSITIONS_FILE",
                str(Settings.BASE_DIR / "config" / "arm_positions.json"),
            )

        import json

        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    positions = json.load(f)
                logging.getLogger("fabric_detection.settings").info(
                    f"Loaded custom arm positions from {file_path}"
                )
                return positions
        except Exception as e:
            logging.getLogger("fabric_detection.settings").error(
                f"Error loading custom positions: {e}"
            )

        return None

    @classmethod
    def initialize(cls):
        """Initialize settings and perform startup checks"""
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(cls.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Check for custom arm positions
        custom_positions = cls.load_custom_positions()
        if custom_positions:
            cls.ARM_POSITIONS = custom_positions

        # Check CUDA
        cls.check_cuda()

        return cls


# Test code for standalone testing
if __name__ == "__main__":
    # Configure basic logging to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    logger = logging.getLogger("settings_test")

    # Initialize settings
    settings = Settings.initialize()

    # Print out current settings
    logger.info("Current Configuration:")
    logger.info(f"Project Name: {settings.PROJECT_NAME}")
    logger.info(f"Version: {settings.VERSION}")
    logger.info(f"Model Path: {settings.MODEL_PATH}")
    logger.info(f"Log File: {settings.LOG_FILE}")
    logger.info(f"Device: {settings.DEVICE}")
    logger.info(f"Detection Threshold: {settings.DETECTION_THRESHOLD}")
    logger.info(f"Camera Resolution: {settings.CAMERA_WIDTH}x{settings.CAMERA_HEIGHT}")
    logger.info(f"Window Size: {settings.WINDOW_SIZE}")

    # Print arm positions
    logger.info("Arm Positions:")
    for position_name, position_data in settings.ARM_POSITIONS.items():
        logger.info(f"  {position_name}: {position_data}")
