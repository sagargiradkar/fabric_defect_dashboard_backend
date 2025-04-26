# lib/detector.py
"""
Fabric defect detection module for the Fabric Defect Detection System.

This module handles loading the YOLO model and processing frames to detect
fabric defects like holes, stitches, and seams.
"""

import logging
import numpy as np
import torch
import traceback
import time
import os
from ultralytics import YOLO
from config.settings import Settings


class LiveFabricDefectDetector:
    """
    Fabric defect detector using YOLO model

    Handles loading the model and processing frames to detect fabric defects.
    """

    def __init__(self, model_path=None, class_names=None):
        """
        Initialize the fabric defect detector

        Args:
            model_path: Path to the YOLO model file
            class_names: List of class names for detection
        """
        self.logger = logging.getLogger("fabric_detection.detector")

        try:
            self.logger.debug("Initializing YOLO model...")
            self.model_path = model_path or Settings.MODEL_PATH
            self.class_names = class_names or Settings.CLASS_NAMES

            # Check if model file exists
            if not os.path.exists(self.model_path):
                self.logger.error(f"Model file not found: {self.model_path}")
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            # Load the YOLO model
            self.model = YOLO(self.model_path)

            # Log model information
            self.logger.info(f"YOLO model loaded: {self.model_path}")
            self.logger.info(f"Class names: {self.class_names}")
            self.logger.info(f"Using device: {Settings.DEVICE}")

            # Performance metrics
            self.inference_times = []
            self.max_times_to_keep = 10  # Keep last 10 inference times for average

        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            traceback.print_exc()
            raise

    def predict(self, frame, confidence=None):
        """
        Run prediction on a frame

        Args:
            frame: Image frame to process
            confidence: Confidence threshold (optional)

        Returns:
            Detection results or None on error
        """
        try:
            # Set confidence threshold if provided
            conf = (
                confidence if confidence is not None else Settings.DETECTION_THRESHOLD
            )

            # Measure inference time
            start_time = time.time()

            # Run prediction
            results = self.model.predict(
                source=frame, conf=conf, save=False, show=False
            )

            # Calculate and store inference time
            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)

            # Keep only the last N times
            if len(self.inference_times) > self.max_times_to_keep:
                self.inference_times = self.inference_times[-self.max_times_to_keep :]

            # Log average inference time periodically
            if len(self.inference_times) % 10 == 0:
                avg_time = sum(self.inference_times) / len(self.inference_times)
                self.logger.debug(
                    f"Average inference time: {avg_time:.4f}s ({1/avg_time:.2f} FPS)"
                )

            return results[0]

        except Exception as e:
            self.logger.error(f"Error in prediction: {e}")
            traceback.print_exc()
            return None

    def get_detections(self, frame, confidence_threshold=None):
        """
        Get list of detections with class names and confidence

        Args:
            frame: Image frame to process
            confidence_threshold: Minimum confidence threshold

        Returns:
            List of detections: [{'label': class_name, 'confidence': conf, 'bbox': (x1,y1,x2,y2)}]
        """
        results = self.predict(frame, confidence_threshold)
        if results is None:
            return []

        threshold = confidence_threshold or Settings.DETECTION_THRESHOLD
        detections = []

        for box in results.boxes:
            conf = float(box.conf[0])
            if conf >= threshold:
                class_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                detections.append(
                    {
                        "label": self.class_names[class_id],
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                    }
                )

        return detections

    def draw_detections(self, frame, detections=None, confidence_threshold=None):
        """
        Draw detection boxes on a frame

        Args:
            frame: The frame to draw on
            detections: List of detections (if None, will run detection)
            confidence_threshold: Confidence threshold for detection

        Returns:
            Frame with detection boxes drawn
        """
        # Make a copy of the frame to avoid modifying the original
        display_frame = frame.copy()

        # Get detections if not provided
        if detections is None:
            detections = self.get_detections(frame, confidence_threshold)

        # Draw each detection
        for detection in detections:
            label = detection["label"]
            conf = detection["confidence"]
            x1, y1, x2, y2 = detection["bbox"]

            # Choose color based on defect type
            if label == "Hole":
                color = (0, 0, 255)  # Red for holes
            elif label == "Stitch":
                color = (0, 255, 255)  # Yellow for stitches
            elif label == "Seam":
                color = (0, 255, 0)  # Green for seams
            else:
                color = (255, 0, 0)  # Blue for unknown

            # Draw bounding box
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)

            # Draw label with confidence
            label_text = f"{label} ({conf:.2f})"
            cv2.putText(
                display_frame,
                label_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        return display_frame


# Test code for standalone testing
if __name__ == "__main__":
    # Set up basic logging to console
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Try to load a test image or use a mock image
    import cv2
    import os

    # Try to get model path from environment, or use default
    model_path = os.environ.get("FABRIC_MODEL_PATH", Settings.MODEL_PATH)

    try:
        # Create detector
        detector = LiveFabricDefectDetector(model_path=model_path)

        # First try to load a test image if available
        test_image_path = os.path.join(
            os.path.dirname(__file__), "..", "tests", "data", "test_fabric.jpg"
        )

        if os.path.exists(test_image_path):
            # Load test image
            print(f"Loading test image: {test_image_path}")
            frame = cv2.imread(test_image_path)
        else:
            # Generate mock image
            print("Test image not found, creating mock frame")
            from camera import CameraModule

            camera = CameraModule()
            frame = camera.get_mock_frame(add_shapes=True)

        if frame is not None:
            # Run detection and draw results
            detections = detector.get_detections(frame)
            result_frame = detector.draw_detections(frame, detections)

            # Print detections
            print(f"Found {len(detections)} defects:")
            for i, detection in enumerate(detections):
                print(f"  {i+1}. {detection['label']} ({detection['confidence']:.2f})")

            # Show image with detections
            cv2.imshow("Fabric Defect Detection", result_frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("Failed to load or create test image")

    except Exception as e:
        print(f"Error in detector test: {e}")
        traceback.print_exc()
