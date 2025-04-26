# tests/test_detector.py
"""
Tests for the fabric defect detector module of the Fabric Defect Detection System.
"""

import pytest
import numpy as np
import os
import sys
import logging
from unittest.mock import MagicMock, patch

# Add parent directory to path to import from lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Settings
from utils.logging_setup import setup_logging

# Set up logging for tests
setup_logging(log_file=None, console_level=logging.WARNING)

# Create mocks for YOLO and results
class MockYOLOResults:
    def __init__(self, num_detections=2):
        self.boxes = MockBoxes(num_detections)

class MockBoxes:
    def __init__(self, num_detections=2):
        self.conf = [np.array([0.95]) for _ in range(num_detections)]
        self.cls = [np.array([i % 3]) for i in range(num_detections)]  # 0=Hole, 1=Stitch, 2=Seam
        self.xyxy = [np.array([[100, 100, 200, 200]]) for _ in range(num_detections)]

class MockYOLO:
    def __init__(self, model_path):
        self.model_path = model_path
    
    def predict(self, source, conf, save=False, show=False):
        # Return a list with a single results object (YOLO standard format)
        return [MockYOLOResults()]

# Test fixtures
@pytest.fixture
def detector_module():
    """Create a detector module for testing with the mock YOLO."""
    with patch('ultralytics.YOLO', MockYOLO):
        # Import here to apply the patch
        from lib.detector import LiveFabricDefectDetector
        
        # Create a mock model file
        model_path = "mock_model.pt"
        with open(model_path, "w") as f:
            f.write("mock model")
        
        # Create detector
        detector = LiveFabricDefectDetector(
            model_path=model_path,
            class_names=["Hole", "Stitch", "Seam"]
        )
        
        yield detector
        
        # Cleanup
        if os.path.exists(model_path):
            os.remove(model_path)

@pytest.fixture
def test_frame():
    """Create a test frame for detection."""
    return np.zeros((480, 640, 3), dtype=np.uint8)

# Tests
def test_detector_init(detector_module):
    """Test detector module initialization."""
    assert detector_module is not None
    assert detector_module.model is not None
    assert detector_module.class_names == ["Hole", "Stitch", "Seam"]
    assert len(detector_module.inference_times) == 0

def test_detector_predict(detector_module, test_frame):
    """Test detection prediction."""
    result = detector_module.predict(test_frame)
    assert result is not None
    
    # Check inference times are recorded
    assert len(detector_module.inference_times) == 1
    assert detector_module.inference_times[0] > 0

def test_detector_get_detections(detector_module, test_frame):
    """Test getting detections with classes and confidence."""
    detections = detector_module.get_detections(test_frame)
    
    assert len(detections) == 2  # Our mock returns 2 detections
    
    # Check structure of detections
    for detection in detections:
        assert 'label' in detection
        assert 'confidence' in detection
        assert 'bbox' in detection
        
        assert detection['label'] in ["Hole", "Stitch", "Seam"]
        assert 0 <= detection['confidence'] <= 1
        assert len(detection['bbox']) == 4

def test_detector_confidence_threshold(detector_module, test_frame):
    """Test confidence threshold filtering."""
    # Set a very high threshold to exclude all detections
    detections = detector_module.get_detections(test_frame, confidence_threshold=0.99)
    assert len(detections) == 0
    
    # Set a very low threshold to include all detections
    detections = detector_module.get_detections(test_frame, confidence_threshold=0.0)
    assert len(detections) == 2

@patch('cv2.rectangle')
@patch('cv2.putText')
def test_detector_draw_detections(mock_putText, mock_rectangle, detector_module, test_frame):
    """Test drawing detections on frame."""
    # Test with explicit detections
    detections = [
        {'label': 'Hole', 'confidence': 0.95, 'bbox': (10, 20, 30, 40)},
        {'label': 'Stitch', 'confidence': 0.85, 'bbox': (50, 60, 70, 80)}
    ]
    
    result_frame = detector_module.draw_detections(test_frame, detections)
    
    # Check result frame is returned and cv2 drawing methods called
    assert result_frame is not None
    assert mock_rectangle.call_count == 2
    assert mock_putText.call_count == 2
    
    # Test auto-detection
    detector_module.draw_detections(test_frame)
    # 2 more calls for each method (2 detections)
    assert mock_rectangle.call_count == 4
    assert mock_putText.call_count == 4

def test_detector_inference_time_tracking(detector_module, test_frame):
    """Test inference time tracking."""
    # Run several predictions
    for _ in range(12):  # More than max_times_to_keep
        detector_module.predict(test_frame)
    
    # Should keep only last 10 (default max_times_to_keep)
    assert len(detector_module.inference_times) == 10
    
    # All times should be positive
    for time in detector_module.inference_times:
        assert time > 0

def test_detector_model_not_found():
    """Test error handling when model file is not found."""
    with patch('ultralytics.YOLO', MockYOLO):
        from lib.detector import LiveFabricDefectDetector
        
        with pytest.raises(FileNotFoundError):
            LiveFabricDefectDetector(model_path="nonexistent_model.pt")

@patch('lib.detector.YOLO')
def test_detector_prediction_exception(mock_yolo, detector_module, test_frame):
    """Test exception handling during prediction."""
    # Setup mock to raise exception during predict
    detector_module.model.predict.side_effect = Exception("Test exception")
    
    # Should return None on exception
    result = detector_module.predict(test_frame)
    assert result is None
    
    # Should return empty list for detections
    detections = detector_module.get_detections(test_frame)
    assert detections == []

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
