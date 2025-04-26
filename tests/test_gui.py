# tests/test_gui.py
"""
Tests for the GUI module of the Fabric Defect Detection System.
"""

import pytest
import os
import sys
import logging
import tkinter as tk
from unittest.mock import MagicMock, patch

# Add parent directory to path to import from lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Settings
from utils.logging_setup import setup_logging

# Set up logging for tests
setup_logging(log_file=None, console_level=logging.WARNING)

# Skip GUI tests if running in headless environment
pytestmark = pytest.mark.skipif(
    "DISPLAY" not in os.environ and os.name != "nt",
    reason="GUI tests require a display"
)

# Mock classes for dependencies
class MockCameraModule:
    def __init__(self, *args, **kwargs):
        self.initialized = True
        self.width = 640
        self.height = 480
    
    def initialize(self):
        return True
    
    def capture_frame(self):
        import numpy as np
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def get_mock_frame(self, add_shapes=True):
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        if add_shapes:
            # Add a simple shape
            frame[100:200, 100:200] = 255
        return frame
    
    def close(self):
        pass

class MockDetector:
    def __init__(self, *args, **kwargs):
        pass
    
    def get_detections(self, frame, confidence_threshold=None):
        return [
            {'label': 'Hole', 'confidence': 0.95, 'bbox': (100, 100, 200, 200)}
        ]
    
    def draw_detections(self, frame, detections=None, confidence_threshold=None):
        return frame

class MockRobotArm:
    def __init__(self, *args, **kwargs):
        self.arm_ready = True
        self.is_busy = False
    
    def get_status(self):
        return {
            'ready': True,
            'busy': False,
            'simulation': True,
            'position': "home",
            'last_action': 0,
            'gripper': 'closed'
        }
    
    def handle_object(self, defective=True):
        pass
    
    def emergency_stop(self):
        pass

# Test fixtures
@pytest.fixture
def mock_dependencies():
    """Mock all dependencies for GUI testing."""
    with patch('lib.camera.CameraModule', MockCameraModule):
        with patch('lib.detector.LiveFabricDefectDetector', MockDetector):
            with patch('lib.robot_arm.RobotArmController', MockRobotArm):
                with patch('lib.gui.cv2') as mock_cv2:
                    mock_cv2.cvtColor = lambda frame, _: frame
                    mock_cv2.resize = lambda frame, dim, **kwargs: frame
                    mock_cv2.LINE_AA = 0
                    yield

@pytest.fixture
def gui_module(mock_dependencies):
    """Create a GUI module for testing."""
    # Import here to apply the mocks
    from lib.gui import FabricDetectionGUI
    
    # Create a root window for testing
    root = tk.Tk()
    root.geometry("800x600")
    
    # Create GUI
    gui = FabricDetectionGUI(root)
    
    # Return the GUI module
    yield gui
    
    # Clean up
    root.destroy()

# Tests
def test_gui_init(gui_module):
    """Test GUI initialization."""
    assert gui_module is not None
    assert gui_module.root is not None
    assert gui_module.camera is not None
    assert gui_module.detector is not None
    assert gui_module.robot_arm is not None
    
    # Check that main components were created
    assert gui_module.frame_left is not None
    assert gui_module.frame_right is not None
    assert gui_module.video_label is not None
    assert gui_module.control_panel is not None

def test_gui_update_frame(gui_module):
    """Test frame update mechanism."""
    # Call update_frame directly
    gui_module.update_frame()
    
    # Check that the video_label has an image
    assert hasattr(gui_module.video_label, 'image')
    assert gui_module.video_label.image is not None

def test_gui_process_frame(gui_module):
    """Test frame processing."""
    # Get a frame to process
    frame = gui_module.camera.get_mock_frame()
    
    # Process the frame
    processed = gui_module.process_frame(frame)
    
    # Should return a valid frame
    assert processed is not None
    assert processed.shape == frame.shape

def test_gui_toggle_detection(gui_module):
    """Test toggling detection on/off."""
    # Initially detection should be on
    assert gui_module.detection_active == True
    
    # Toggle off
    gui_module.toggle_detection()
    assert gui_module.detection_active == False
    
    # Toggle back on
    gui_module.toggle_detection()
    assert gui_module.detection_active == True

def test_gui_toggle_processing(gui_module):
    """Test toggling automated processing on/off."""
    # Initially processing should be off
    assert gui_module.auto_processing == False
    
    # Toggle on
    gui_module.toggle_processing()
    assert gui_module.auto_processing == True
    
    # Toggle back off
    gui_module.toggle_processing()
    assert gui_module.auto_processing == False

def test_gui_emergency_stop(gui_module):
    """Test emergency stop functionality."""
    # Initially buttons should be in normal state
    normal_bg = gui_module.emergency_button.cget('bg')
    
    # Trigger emergency stop
    gui_module.emergency_stop()
    
    # Button should change color
    assert gui_module.emergency_button.cget('bg') != normal_bg
    
    # Processing should be stopped
    assert gui_module.auto_processing == False

def test_gui_status_update(gui_module):
    """Test status updates in UI."""
    # Set a status
    gui_module.update_status("Test status message")
    
    # Status should be displayed
    assert gui_module.status_label.cget('text') == "Test status message"

def test_gui_log_message(gui_module):
    """Test logging messages to UI."""
    # Initially log should be empty
    initial_log = gui_module.log_text.get("1.0", tk.END)
    
    # Log a message
    gui_module.log_message("Test log message")
    
    # Message should be in log
    updated_log = gui_module.log_text.get("1.0", tk.END)
    assert len(updated_log) > len(initial_log)
    assert "Test log message" in updated_log

def test_gui_process_defects(gui_module):
    """Test defect processing logic."""
    # Set up mock frame with detections
    frame = gui_module.camera.get_mock_frame()
    detections = [{'label': 'Hole', 'confidence': 0.95, 'bbox': (100, 100, 200, 200)}]
    
    # Process defects
    gui_module.process_defects(frame, detections)
    
    # Should log a defect found message
    log_text = gui_module.log_text.get("1.0", tk.END)
    assert "Defect detected" in log_text

def test_gui_robot_control(gui_module):
    """Test robot control functionality."""
    # Test manual robot control
    gui_module.handle_defect()
    gui_module.handle_good_item()
    
    # Should update log messages
    log_text = gui_module.log_text.get("1.0", tk.END)
    assert "Sending defective item" in log_text or "Handling defective item" in log_text

def test_gui_reset_system(gui_module):
    """Test system reset functionality."""
    # First activate auto processing
    gui_module.auto_processing = True
    
    # Reset system
    gui_module.reset_system()
    
    # Auto processing should be off
    assert gui_module.auto_processing == False
    
    # Status should be updated
    assert "System reset" in gui_module.status_label.cget('text')

def test_gui_system_shutdown(gui_module):
    """Test system shutdown functionality."""
    # Mock root.destroy to check if called
    gui_module.root.destroy = MagicMock()
    
    # Call shutdown
    gui_module.system_shutdown()
    
    # Should call root.destroy
    gui_module.root.destroy.assert_called_once()

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
