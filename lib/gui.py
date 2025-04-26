# lib/gui.py
"""
GUI module for the Fabric Defect Detection System

This module handles the graphical user interface for the fabric defect detection system,
including displaying camera feed, detection results, and robot arm controls.
"""

import logging
import time
import threading
import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
from config.settings import Settings

class FabricDetectionGUI:
    """
    Graphical user interface for fabric defect detection system
    
    Provides a user interface for visualizing camera feed, detection results,
    and robot arm control.
    """
    
    def __init__(self, camera, detector, robot_arm):
        """
        Initialize the GUI
        
        Args:
            camera: CameraModule instance
            detector: LiveFabricDefectDetector instance
            robot_arm: RobotArmController instance
        """
        self.logger = logging.getLogger("fabric_detection.gui")
        
        # Store module references
        self.camera = camera
        self.detector = detector
        self.robot_arm = robot_arm
        
        # Detection state
        self.last_detection_time = 0
        self.last_process_time = 0
        self.detection_cooldown = Settings.DETECTION_COOLDOWN
        self.detection_threshold = Settings.DETECTION_THRESHOLD
        self.detected_defects = []
        self.auto_mode = False
        
        # Initialize Tkinter components
        self._initialize_ui()
    
    def _initialize_ui(self):
        """Initialize the user interface components"""
        # Initialize root window
        self.root = tk.Tk()
        self.root.title(Settings.PROJECT_NAME)
        self.root.geometry(Settings.WINDOW_SIZE)
        self.root.configure(bg="#f0f0f0")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Title Frame
        self._create_title_frame()
        
        # Content Frame (Camera + Info + Controls)
        self._create_content_frame()
        
        # Status Bar
        self._create_status_bar()
    
    def _create_title_frame(self):
        """Create the title frame"""
        self.title_frame = tk.Frame(self.root, bg="#004080", height=50)
        self.title_frame.pack(fill="x")
        title_label = tk.Label(
            self.title_frame, 
            text=Settings.PROJECT_NAME, 
            font=("Helvetica", 20, "bold"), 
            fg="white", 
            bg="#004080"
        )
        title_label.pack(pady=10)
    
    def _create_content_frame(self):
        """Create the content frame with camera view, info panel, and controls"""
        self.content_frame = tk.Frame(self.root, bg="white")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Camera Frame
        self.camera_label = tk.Label(self.content_frame, bg="black")
        self.camera_label.grid(row=0, column=0, padx=10, rowspan=2)
        
        # Info Frame
        self._create_info_frame()
        
        # Control Frame
        self._create_control_frame()
    
    def _create_info_frame(self):
        """Create the information panel"""
        self.info_frame = tk.Frame(self.content_frame, bg="white")
        self.info_frame.grid(row=0, column=1, sticky="n", pady=10)
        
        # Classification label
        self.class_label = tk.Label(
            self.info_frame, 
            text="Initializing...", 
            font=("Arial", 14), 
            bg="white", 
            fg="green", 
            wraplength=300, 
            justify="left"
        )
        self.class_label.pack(pady=10)
        
        # Robot arm status
        status_text = "Robot Arm: " + ("Ready" if self.robot_arm.arm_ready else "Not Connected")
        status_color = "green" if self.robot_arm.arm_ready else "red"
        
        self.robot_status = tk.Label(
            self.info_frame,
            text=status_text,
            font=("Arial", 12),
            bg="white",
            fg=status_color
        )
        self.robot_status.pack(pady=10)
        
        # Version info
        version_label = tk.Label(
            self.info_frame,
            text=f"Version: {Settings.VERSION}",
            font=("Arial", 10),
            bg="white",
            fg="#666666"
        )
        version_label.pack(pady=(20, 10))
    
    def _create_control_frame(self):
        """Create the control panel"""
        self.control_frame = tk.Frame(self.content_frame, bg="white")
        self.control_frame.grid(row=1, column=1, sticky="n", pady=10)
        
        # Auto mode toggle
        self.auto_var = tk.BooleanVar(value=False)
        self.auto_check = tk.Checkbutton(
            self.control_frame,
            text="Automatic Robot Control",
            variable=self.auto_var,
            command=self.toggle_auto_mode,
            font=("Arial", 12)
        )
        self.auto_check.pack(pady=5)
        
        # Manual control buttons
        self._create_manual_controls()
        
        # Movement Test Button
        tk.Button(
            self.control_frame,
            text="Test Pick & Place Sequence",
            command=self.test_robot_movement,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 12)
        ).pack(pady=10)
        
        # Threshold control
        self._create_threshold_controls()
    
    def _create_manual_controls(self):
        """Create manual control buttons"""
        self.manual_frame = tk.Frame(self.control_frame, bg="white")
        self.manual_frame.pack(pady=10)
        
        # Defective button
        tk.Button(
            self.manual_frame,
            text="Handle as Defective",
            command=lambda: self.manual_robot_action(defective=True),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Good button
        tk.Button(
            self.manual_frame,
            text="Handle as Good",
            command=lambda: self.manual_robot_action(defective=False),
            bg="#2ecc71",
            fg="white",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Home button
        tk.Button(
            self.manual_frame,
            text="Home Position",
            command=self.reset_robot,
            bg="#3498db",
            fg="white",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_threshold_controls(self):
        """Create threshold adjustment controls"""
        self.threshold_frame = tk.Frame(self.control_frame, bg="white")
        self.threshold_frame.pack(pady=10, fill="x")
        
        tk.Label(
            self.threshold_frame,
            text="Detection Threshold:",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        self.threshold_var = tk.DoubleVar(value=self.detection_threshold)
        self.threshold_slider = tk.Scale(
            self.threshold_frame,
            from_=0.1,
            to=0.9,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            command=self.update_threshold,
            length=150
        )
        self.threshold_slider.pack(side=tk.LEFT, padx=5)
        
        # Current threshold value label
        self.threshold_value_label = tk.Label(
            self.threshold_frame,
            text=f"{self.detection_threshold:.2f}",
            font=("Arial", 10),
            bg="white",
            width=4
        )
        self.threshold_value_label.pack(side=tk.LEFT, padx=5)
    
    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = tk.Label(
            self.root, 
            text="System ready", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            bg="#d9d9d9"
        )
        self.status_bar.pack(side="bottom", fill="x")
    
    def toggle_auto_mode(self):
        """Toggle automatic robot control mode"""
        self.auto_mode = self.auto_var.get()
        status = "Enabled" if self.auto_mode else "Disabled"
        self.logger.info(f"Automatic robot control {status}")
        self.update_status(f"Auto mode: {status}")
    
    def update_threshold(self, value):
        """Update detection threshold from slider"""
        self.detection_threshold = float(value)
        self.threshold_value_label.config(text=f"{self.detection_threshold:.2f}")
        self.logger.info(f"Detection threshold set to {self.detection_threshold}")
    
    def test_robot_movement(self):
        """Test function to manually trigger the complete pick and place sequence"""
        if not self.robot_arm.arm_ready or self.robot_arm.is_busy:
            self.update_status("Robot arm busy or not connected")
            return
        
        self.update_status("Testing pick and place sequence...")
        threading.Thread(target=self.robot_arm.handle_object, args=(True,)).start()
    
    def manual_robot_action(self, defective=True):
        """Trigger manual robot arm action"""
        if not self.robot_arm.arm_ready:
            self.update_status("Robot arm not connected!")
            return
        
        if self.robot_arm.is_busy:
            self.update_status("Robot arm is busy!")
            return
        
        self.update_status(f"Manual control: {'Defective' if defective else 'Good'} item")
        threading.Thread(target=self.robot_arm.handle_object, args=(defective,)).start()
    
    def reset_robot(self):
        """Reset robot arm to home position"""
        if not self.robot_arm.arm_ready or self.robot_arm.is_busy:
            return
        
        self.update_status("Moving to home position")
        threading.Thread(target=self.robot_arm.move_to_position, 
                          args=(self.robot_arm.positions["home"],)).start()
        threading.Thread(target=self.robot_arm.gripper_close).start()
    
    def update_status(self, message):
        """Update status bar with message"""
        self.status_bar.config(text=message)
        self.logger.info(message)
    
    def update_frame(self):
        """Update the camera frame and process detections"""
        try:
            # Get frame from camera
            frame = self.camera.capture_frame()
            
            if frame is None:
                self.logger.error("Failed to capture frame")
                # Re-schedule next frame and return
                self.root.after(int(1000/Settings.FRAME_RATE), self.update_frame)
                return
            
            # Make a copy for drawing on
            display_frame = frame.copy()
            
            # Process frame with detection at reduced rate to improve performance
            current_time = time.time()
            process_frame = False
            
            if not hasattr(self, 'last_process_time') or current_time - self.last_process_time >= 0.5:
                process_frame = True
                self.last_process_time = current_time
            
            if process_frame:
                # Get detections
                detections = self.detector.get_detections(frame, self.detection_threshold)
                
                # Update detected defects list
                self.detected_defects = [detection['label'] for detection in detections]
                
                # Process for robot control
                self._handle_detections()
                
                # Draw detection boxes
                for detection in detections:
                    label = detection['label']
                    conf = detection['confidence']
                    x1, y1, x2, y2 = detection['bbox']
                    
                    # Draw bounding box (red for high confidence)
                    color = (0, 0, 255)  # BGR format
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw label with confidence
                    label_text = f"{label} ({conf:.2f})"
                    cv2.putText(display_frame, label_text, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Convert to PIL Image for display in Tkinter
            display_img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(display_img)
            img_tk = ImageTk.PhotoImage(image=img)
            self.camera_label.config(image=img_tk)
            self.camera_label.image = img_tk  # Keep reference to prevent garbage collection
            
            # Update classification info
            self._update_classification_info()
            
            # Update robot status
            self._update_robot_status()
            
        except Exception as e:
            self.logger.error(f"Error in frame processing: {e}")
            import traceback
            traceback.print_exc()
        
        # Schedule next frame update
        self.root.after(int(1000/Settings.FRAME_RATE), self.update_frame)
    
    def _handle_detections(self):
        """Handle detections for robot control"""
        current_time = time.time()
        time_since_last = current_time - self.last_detection_time
        
        # Only trigger automatic robot control if:
        # 1. Auto mode is enabled
        # 2. Robot arm is ready and not busy
        # 3. Enough time has passed since last detection
        if (self.auto_mode and
            self.robot_arm.arm_ready and
            not self.robot_arm.is_busy and
            time_since_last > self.detection_cooldown):
            
            # If we have any defects, handle as defective
            if self.detected_defects:
                self.update_status(f"Auto: Defect detected - handling as defective")
                threading.Thread(target=self.robot_arm.handle_object, args=(True,)).start()
                self.last_detection_time = current_time
            # If we've seen no defects for a while, handle as good
            elif time_since_last > self.detection_cooldown * 2:
                self.update_status(f"Auto: No defects - handling as good")
                threading.Thread(target=self.robot_arm.handle_object, args=(False,)).start()
                self.last_detection_time = current_time
    
    def _update_classification_info(self):
        """Update the classification info display"""
        if self.detected_defects:
            # Create a set to avoid duplicates and join with newlines
            unique_defects = set(self.detected_defects)
            text = "Detected Defects:\n" + "\n".join(unique_defects)
            self.class_label.config(text=text, fg="red")
        else:
            self.class_label.config(text="No Defects Detected", fg="green")
    
    def _update_robot_status(self):
        """Update the robot arm status display"""
        robot_status_text = "Robot Arm: "
        if not self.robot_arm.arm_ready:
            robot_status_text += "Not Connected"
            robot_status_color = "red"
        elif self.robot_arm.is_busy:
            robot_status_text += "Busy"
            robot_status_color = "orange"
        else:
            robot_status_text += "Ready"
            robot_status_color = "green"
        
        self.robot_status.config(text=robot_status_text, fg=robot_status_color)
    
    def on_closing(self):
        """Handle window close event"""
        self.logger.info("Application closing")
        
        # Reset arm position if possible
        if self.robot_arm.arm_ready and not self.robot_arm.is_busy:
            self.robot_arm.move_to_position(self.robot_arm.positions["home"])
            self.robot_arm.gripper_close()
        
        # Close camera
        if self.camera:
            self.camera.close()
        
        # Destroy window
        self.root.destroy()
    
    def run(self):
        """Start the GUI main loop"""
        self.logger.info("Starting Fabric Defect Detection GUI...")
        
        # Start the frame update loop
        self.update_frame()
        
        # Start the main event loop
        self.root.mainloop()


# Test code for standalone testing of the GUI module
if __name__ == "__main__":
    # This allows testing the GUI in isolation with mock objects
    import sys
    from unittest.mock import MagicMock
    from utils.logging_setup import setup_logging
    
    # Set up logging
    logger = setup_logging()
    logger.info("Testing GUI module in standalone mode")
    
    # Create mock objects for testing
    mock_camera = MagicMock()
    mock_camera.capture_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
    
    mock_detector = MagicMock()
    mock_detector.get_detections.return_value = []
    
    mock_robot_arm = MagicMock()
    mock_robot_arm.arm_ready = True
    mock_robot_arm.is_busy = False
    mock_robot_arm.positions = {"home": {0: 120, 1: 45, 2: 45}}
    
    # Create and run GUI
    gui = FabricDetectionGUI(mock_camera, mock_detector, mock_robot_arm)
    
    # After a few seconds, simulate a detection to test the UI updates
    def simulate_detection():
        mock_detector.get_detections.return_value = [
            {'label': 'Hole', 'confidence': 0.85, 'bbox': (100, 100, 200, 200)}
        ]
        logger.info("Simulated detection added")
    
    gui.root.after(3000, simulate_detection)
    
    # Run the GUI
    gui.run()
