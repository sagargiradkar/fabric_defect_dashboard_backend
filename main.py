#!/usr/bin/env python3
# main.py
"""
Fabric Defect Detection System - Main Application

This is the entry point for the Fabric Defect Detection System,
which integrates camera input, defect detection, and robotic arm
control for automated fabric quality inspection.
"""

import os
import sys
import time
import argparse
import threading
import logging
import tkinter as tk
from pathlib import Path

# Import configuration and utilities
from config.settings import Settings
from utils.logging_setup import setup_logging, log_system_info

# Import application modules
from lib.camera import CameraModule
from lib.detector import LiveFabricDefectDetector
from lib.robot_arm import RobotArmController
from lib.gui import FabricDetectionGUI

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Fabric Defect Detection System")
    
    # Mode arguments
    parser.add_argument('--headless', action='store_true', 
                        help='Run in headless mode (no GUI)')
    parser.add_argument('--simulation', action='store_true',
                        help='Run in simulation mode (no hardware required)')
    parser.add_argument('--test', action='store_true',
                        help='Run system tests and exit')
    
    # Configuration arguments
    parser.add_argument('--config', type=str, default=None,
                        help='Path to custom configuration file')
    parser.add_argument('--model', type=str, default=None,
                        help='Path to custom detection model file')
    parser.add_argument('--log-level', type=str, default=None,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    
    # Camera arguments
    parser.add_argument('--camera-width', type=int, default=None,
                        help='Camera width in pixels')
    parser.add_argument('--camera-height', type=int, default=None,
                        help='Camera height in pixels')
    
    # Processing arguments
    parser.add_argument('--confidence', type=float, default=None,
                        help='Detection confidence threshold (0.0-1.0)')
    
    return parser.parse_args()

def configure_application(args):
    """Configure application settings based on arguments"""
    # If custom config file provided, load it
    if args.config:
        Settings.load_config(args.config)
    
    # Override settings with command line arguments if provided
    if args.model:
        Settings.MODEL_PATH = args.model
    
    if args.log_level:
        Settings.LOG_LEVEL = getattr(logging, args.log_level)
    
    if args.camera_width:
        Settings.CAMERA_WIDTH = args.camera_width
    
    if args.camera_height:
        Settings.CAMERA_HEIGHT = args.camera_height
    
    if args.confidence is not None:
        Settings.CONFIDENCE_THRESHOLD = args.confidence
    
    # Ensure model path exists
    model_path = Path(Settings.MODEL_PATH)
    if not model_path.exists():
        print(f"Error: Model file not found at {Settings.MODEL_PATH}")
        print("Please provide a valid model path with --model or update the configuration")
        sys.exit(1)
    
    # Configure logging
    logger = setup_logging(log_file=Settings.LOG_FILE, 
                          console_level=Settings.LOG_LEVEL)
    
    return logger

def run_tests():
    """Run system tests"""
    import pytest
    
    print("Running system tests...")
    
    # Define test directory
    test_dir = os.path.join(os.path.dirname(__file__), "tests")
    
    # Run tests with pytest
    return pytest.main(["-xvs", test_dir])

def run_gui_application(logger):
    """Run the application with GUI"""
    logger.info("Starting Fabric Defect Detection System in GUI mode")
    
    # Initialize main application window
    root = tk.Tk()
    root.title("Fabric Defect Detection System")
    
    # Configure window
    root.geometry(f"{Settings.GUI_WIDTH}x{Settings.GUI_HEIGHT}")
    root.minsize(800, 600)
    
    try:
        # Create GUI with components
        app = FabricDetectionGUI(root)
        
        # Log system info
        log_system_info()
        
        # Start GUI main loop
        logger.info("GUI initialized, starting main loop")
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Fatal error in GUI application: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("GUI application shutdown complete")

def run_headless_application(logger, simulation_mode=False):
    """Run the application in headless mode"""
    logger.info(f"Starting Fabric Defect Detection System in headless mode (simulation={simulation_mode})")
    
    # Initialize components
    camera = None
    detector = None
    robot_arm = None
    
    try:
        # Initialize camera
        logger.info("Initializing camera...")
        camera = CameraModule(
            width=Settings.CAMERA_WIDTH,
            height=Settings.CAMERA_HEIGHT,
            format_rgb=True
        )
        
        if not camera.initialize():
            if simulation_mode:
                logger.warning("Camera initialization failed, but continuing in simulation mode")
            else:
                logger.error("Camera initialization failed, exiting")
                return 1
        
        # Initialize detector
        logger.info("Initializing detector...")
        detector = LiveFabricDefectDetector(
            model_path=Settings.MODEL_PATH,
            class_names=Settings.CLASS_NAMES
        )
        
        # Initialize robot arm
        logger.info("Initializing robot arm...")
        robot_arm = RobotArmController(simulation_mode=simulation_mode)
        
        if not robot_arm.arm_ready and not simulation_mode:
            logger.error("Robot arm initialization failed, exiting")
            return 1
        
        # Log system info
        log_system_info()
        
        # Main processing loop
        logger.info("Starting main processing loop")
        running = True
        
        while running:
            try:
                # Capture frame
                frame = camera.capture_frame()
                if frame is None:
                    if simulation_mode:
                        frame = camera.get_mock_frame(add_shapes=True)
                    else:
                        logger.error("Failed to capture frame")
                        time.sleep(1)
                        continue
                
                # Get detections
                detections = detector.get_detections(
                    frame, 
                    confidence_threshold=Settings.CONFIDENCE_THRESHOLD
                )
                
                # Process detections
                if detections:
                    logger.info(f"Detected {len(detections)} defects")
                    
                    # Draw detections on frame (if we had display in headless mode)
                    # frame_with_detections = detector.draw_detections(frame, detections)
                    
                    # Handle the defective item with robot arm
                    if not robot_arm.is_busy:
                        logger.info("Processing defective item")
                        threading.Thread(target=robot_arm.handle_object, 
                                        args=(True,)).start()
                else:
                    # No defects, handle as good item
                    logger.info("No defects detected, item is good")
                    if not robot_arm.is_busy:
                        threading.Thread(target=robot_arm.handle_object, 
                                        args=(False,)).start()
                
                # Sleep for the processing interval
                time.sleep(Settings.PROCESSING_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down")
                running = False
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                time.sleep(1)  # Avoid spam if persistent error
        
    except Exception as e:
        logger.critical(f"Fatal error in headless application: {e}", exc_info=True)
        return 1
    finally:
        # Clean up resources
        logger.info("Shutting down and cleaning up resources")
        
        if camera:
            camera.close()
        
        if robot_arm and robot_arm.arm_ready:
            # Move arm to home position for safety
            if not robot_arm.is_busy and robot_arm.current_position != "home":
                logger.info("Moving robot arm to home position")
                robot_arm.move_to_position(robot_arm.positions["home"])
    
    logger.info("Headless application shutdown complete")
    return 0

def main():
    """Main application entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Run tests if requested
    if args.test:
        return run_tests()
    
    # Configure application settings and logging
    logger = configure_application(args)
    
    # Run in appropriate mode
    if args.headless:
        return run_headless_application(logger, simulation_mode=args.simulation)
    else:
        run_gui_application(logger)
        return 0

if __name__ == "__main__":
    sys.exit(main())
