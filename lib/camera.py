# lib/camera.py
"""
Camera handling module for the Fabric Defect Detection System.

This module manages camera initialization, configuration, and frame capture
using the PiCamera2 library.
"""

import logging
import time
import cv2
import numpy as np
from config.settings import Settings

class CameraModule:
    """
    Camera handling module for fabric detection
    
    Manages camera initialization, configuration, and frame capture.
    """
    
    def __init__(self, width=None, height=None, format_rgb=True):
        """
        Initialize the camera module
        
        Args:
            width: Camera width resolution
            height: Camera height resolution
            format_rgb: Whether to use RGB format (vs. RGBA)
        """
        self.logger = logging.getLogger("fabric_detection.camera")
        
        # Set camera dimensions
        self.width = width or Settings.CAMERA_WIDTH
        self.height = height or Settings.CAMERA_HEIGHT
        self.format_rgb = format_rgb
        
        # Camera object
        self.camera = None
        self.initialized = False
        
        # Performance metrics
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0
        
    def initialize(self):
        """
        Initialize the camera
        
        Returns:
            bool: True if camera was initialized successfully
        """
        try:
            # Import PiCamera2 inside function to avoid immediate import error
            from picamera2 import Picamera2
            
            self.logger.info(f"Initializing camera with resolution {self.width}x{self.height}")
            self.camera = Picamera2()
            
            # Create a camera configuration
            format_str = "RGB888" if self.format_rgb else "RGBA8888"
            camera_config = self.camera.create_preview_configuration(
                main={"size": (self.width, self.height), "format": format_str}
            )
            self.camera.configure(camera_config)
            self.logger.info("Camera configuration successful!")
            
            # Start camera
            self.camera.start()
            self.logger.info("Camera started")
            time.sleep(1)  # Give camera time to initialize
            
            self.initialized = True
            self.start_time = time.time()
            self.logger.info("Camera initialization successful.")
            return True
            
        except ImportError:
            self.logger.error("PiCamera2 module not available")
            return False
        except Exception as e:
            self.logger.error(f"Camera initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def capture_frame(self):
        """
        Capture a frame from the camera
        
        Returns:
            numpy.ndarray: Captured frame or None on error
        """
        if not self.initialized or self.camera is None:
            self.logger.error("Camera not initialized")
            return None
            
        try:
            # Capture frame
            frame = self.camera.capture_array()
            
            # Update frame metrics
            self.frame_count += 1
            elapsed = time.time() - self.start_time
            if elapsed >= 5.0:  # Update FPS every 5 seconds
                self.fps = self.frame_count / elapsed
                self.logger.debug(f"Camera capturing at {self.fps:.2f} FPS")
                self.frame_count = 0
                self.start_time = time.time()
            
            # If we get 4 channels but need 3, convert to RGB
            if self.format_rgb and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
                
            return frame
            
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def close(self):
        """Close the camera and release resources"""
        if self.camera is not None:
            try:
                self.camera.stop()
                self.logger.info("Camera stopped")
                self.camera.close()
                self.logger.info("Camera closed successfully")
                self.initialized = False
            except Exception as e:
                self.logger.error(f"Error closing camera: {e}")

    def get_mock_frame(self, add_shapes=True):
        """
        Generate a mock frame for testing without a camera
        
        Args:
            add_shapes: Whether to add test shapes to the frame
            
        Returns:
            numpy.ndarray: Generated mock frame
        """
        # Create blank frame
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        if add_shapes:
            # Add test patterns
            # Add a rectangle that looks like fabric
            frame[:, :] = (200, 200, 220)  # Light blue-ish background
            
            # Add some texture
            for i in range(0, self.height, 4):
                cv2.line(frame, (0, i), (self.width, i), (190, 190, 210), 1)
            
            # Add a simulated "hole" defect
            cv2.circle(frame, (self.width//4, self.height//2), 30, (0, 0, 0), -1)
            
            # Add a simulated "stitch" defect
            cv2.line(frame, (self.width//2, self.height//4), (self.width//2 + 100, self.height//4), 
                    (50, 50, 250), 8)
            
            # Add a simulated "seam" defect
            start_x = 2*self.width//3
            for i in range(self.height//3, 2*self.height//3, 10):
                cv2.line(frame, (start_x, i), (start_x + 50, i), (30, 180, 30), 3)
        
        return frame


# Test code for standalone testing
if __name__ == "__main__":
    # Set up basic logging to console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    # Create camera module
    camera = CameraModule()
    
    # Try to initialize the camera
    if not camera.initialize():
        print("Using mock camera instead")
        
        # Display mock frame instead
        import cv2
        mock_frame = camera.get_mock_frame(add_shapes=True)
        cv2.imshow("Mock Camera Feed", mock_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        # Display live feed
        print("Camera initialized. Press 'q' to quit.")
        
        try:
            while True:
                frame = camera.capture_frame()
                if frame is not None:
                    cv2.imshow("Camera Feed", frame)
                    
                # Break on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            # Clean up
            camera.close()
            cv2.destroyAllWindows()
