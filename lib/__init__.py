# lib/__init__.py
"""
Fabric Defect Detection System library package.

This package contains the core modules for camera handling, defect detection,
robot arm control, and the graphical user interface.
"""

from .camera import CameraModule
from .detector import LiveFabricDefectDetector
from .robot_arm import RobotArmController
from .gui import FabricDetectionGUI

__all__ = [
    'CameraModule',
    'LiveFabricDefectDetector',
    'RobotArmController',
    'FabricDetectionGUI'
]
