# tests/test_camera.py
"""
Tests for the camera handling module of the Fabric Defect Detection System.
"""

import pytest
import numpy as np
import os
import sys
import logging
from unittest.mock import MagicMock, patch

# Add parent directory to path to import from lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.camera import CameraModule
from config.settings import Settings
from utils.logging_setup import setup_logging

# Set up logging for tests
setup_logging(log_file=None, console_level=logging.WARNING)

# Test fixtures
@pytest.fixture
def camera_module():
    """Create a CameraModule instance for testing."""
    return CameraModule(width=640, height=480)

# Mock for PiCamera2
class MockPiCamera2:
    def __init__(self):
        self.started = False
    
    def create_preview_configuration(self, **kwargs):
        return {"mock_config": True}
    
    def configure(self, config):
        pass
    
    def start(self):
        self.started = True
    
    def stop(self):
        self.started = False
    
    def close(self):
        pass
    
    def capture_array(self):
        """Return a mock frame"""
        return np.zeros((480, 640, 3), dtype=np.uint8)

# Tests
def test_camera_init(camera_module):
    """Test camera module initialization."""
    assert camera_module.width == 640
    assert camera_module.height == 480
    assert camera_module.format_rgb == True
    assert camera_module.initialized == False
    assert camera_module.camera is None

@patch('lib.camera.Picamera2', new=MockPiCamera2)
def test_camera_initialize(camera_module):
    """Test camera initialization with mock PiCamera2."""
    result = camera_module.initialize()
    assert result == True
    assert camera_module.initialized == True
    assert camera_module.camera is not None
    assert camera_module.camera.started == True

def test_camera_initialize_fail(camera_module):
    """Test camera initialization failure handling."""
    # Import error case is simulated by not patching
    result = camera_module.initialize()
    assert result == False
    assert camera_module.initialized == False

@patch('lib.camera.Picamera2', new=MockPiCamera2)
def test_camera_capture_frame(camera_module):
    """Test camera frame capture with mock camera."""
    camera_module.initialize()
    frame = camera_module.capture_frame()
    
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)

def test_camera_capture_frame_not_initialized(camera_module):
    """Test capture frame behavior when camera is not initialized."""
    frame = camera_module.capture_frame()
    assert frame is None

@patch('lib.camera.Picamera2', new=MockPiCamera2)
def test_camera_close(camera_module):
    """Test camera close functionality."""
    camera_module.initialize()
    assert camera_module.initialized == True
    
    camera_module.close()
    assert camera_module.initialized == False

def test_get_mock_frame(camera_module):
    """Test mock frame generation."""
    # Without shapes
    frame = camera_module.get_mock_frame(add_shapes=False)
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)
    assert np.sum(frame) == 0  # Should be all zeros
    
    # With shapes
    frame = camera_module.get_mock_frame(add_shapes=True)
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)
    assert np.sum(frame) > 0  # Should have some content

@patch('lib.camera.Picamera2', new=MockPiCamera2)
def test_camera_performance_metrics(camera_module):
    """Test camera performance metrics tracking."""
    camera_module.initialize()
    
    # Capture a few frames
    for _ in range(10):
        camera_module.capture_frame()
    
    # FPS should be calculated
    assert camera_module.frame_count > 0
    # The FPS might be reset if 5 seconds elapsed during the test
    # so we don't test an exact value

@patch('lib.camera.Picamera2')
def test_camera_exception_handling(mock_picamera, camera_module):
    """Test camera exception handling."""
    # Setup mock to raise an exception
    mock_picamera.side_effect = Exception("Test exception")
    
    result = camera_module.initialize()
    assert result == False
    assert camera_module.initialized == False

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
