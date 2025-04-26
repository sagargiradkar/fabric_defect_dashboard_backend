# utils/logging_setup.py
"""
Logging configuration for the Fabric Defect Detection System.

This module handles the setup and configuration of logging for the entire
application, supporting both console and file output with appropriate
formatting and log rotation.
"""

import logging
import logging.handlers
import os
import sys
import time
from pathlib import Path
from config.settings import Settings

def setup_logging(log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Configure logging for the application with both console and file handlers
    
    Args:
        log_file: Path to the log file (default from Settings)
        console_level: Logging level for console output
        file_level: Logging level for file output
        
    Returns:
        Logger: Root logger configured for the application
    """
    # Get the root logger
    logger = logging.getLogger()
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Set the root logger level to the most verbose level we'll use
    logger.setLevel(min(console_level, file_level))
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(levelname)-8s %(name)-20s: %(message)s'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(name)-20s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Set up file handler if log file path is provided
    log_file_path = log_file or Settings.LOG_FILE
    
    if log_file_path:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Use RotatingFileHandler for log rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path, 
            maxBytes=5*1024*1024,  # 5 MB max file size
            backupCount=5           # Keep 5 backup files
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Log startup message to indicate new session
        logger.info("=" * 80)
        logger.info(f"Logging started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Log file: {log_file_path}")
    
    # Set up module loggers with appropriate levels
    configure_module_loggers()
    
    return logger

def configure_module_loggers():
    """
    Configure specific logging levels for different modules
    """
    # Set third-party libraries to less verbose levels
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("ultralytics").setLevel(logging.INFO)
    logging.getLogger("torch").setLevel(logging.WARNING)
    
    # Configure application module loggers
    fabric_logger = logging.getLogger("fabric_detection")
    fabric_logger.setLevel(logging.DEBUG)

def get_logger(name):
    """
    Get a logger with the specified name, properly prefixed for the application
    
    Args:
        name: Logger name (without the application prefix)
        
    Returns:
        Logger: Configured logger instance
    """
    if name.startswith("fabric_detection."):
        return logging.getLogger(name)
    else:
        return logging.getLogger(f"fabric_detection.{name}")

def log_system_info():
    """
    Log system information for debugging purposes
    """
    logger = logging.getLogger("fabric_detection.system")
    
    try:
        import platform
        import torch
        import cv2
        
        logger.info("=" * 40)
        logger.info("SYSTEM INFORMATION")
        logger.info("=" * 40)
        
        logger.info(f"System: {platform.system()} {platform.release()}")
        logger.info(f"Python: {platform.python_version()}")
        logger.info(f"Platform: {platform.platform()}")
        
        # If CUDA is available, log GPU information
        if torch.cuda.is_available():
            logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA version: {torch.version.cuda}")
            logger.info(f"CUDA arch list: {torch.cuda.get_arch_list() if hasattr(torch.cuda, 'get_arch_list') else 'N/A'}")
        else:
            logger.info("CUDA not available")
        
        logger.info(f"Torch: {torch.__version__}")
        logger.info(f"OpenCV: {cv2.__version__}")
        
        # CPU information
        try:
            from multiprocessing import cpu_count
            logger.info(f"CPU cores: {cpu_count()}")
        except:
            logger.info("Could not determine CPU core count")
            
        # Memory information
        try:
            import psutil
            memory = psutil.virtual_memory()
            logger.info(f"Memory total: {memory.total/1024/1024/1024:.2f} GB")
            logger.info(f"Memory available: {memory.available/1024/1024/1024:.2f} GB")
        except:
            logger.info("Could not determine memory information")
        
        logger.info("=" * 40)
    except Exception as e:
        logger.error(f"Error logging system information: {e}")


# Test code for standalone testing
if __name__ == "__main__":
    # Configure basic settings for testing
    from config.settings import Settings
    
    # Create a test log file in the current directory
    test_log_file = os.path.join(os.path.dirname(__file__), "..", "logs", "test_log.log")
    
    # Setup logging
    logger = setup_logging(test_log_file)
    logger.info("Logging setup test started")
    
    # Get module loggers
    main_logger = get_logger("main")
    camera_logger = get_logger("camera")
    detector_logger = get_logger("detector")
    
    # Test logging at different levels
    main_logger.debug("This is a DEBUG message from main")
    main_logger.info("This is an INFO message from main")
    main_logger.warning("This is a WARNING message from main")
    
    camera_logger.info("Camera module initialized")
    detector_logger.error("Detector test error")
    
    # Log system information
    log_system_info()
    
    # Verify log file was created
    if os.path.exists(test_log_file):
        logger.info(f"Log file successfully created at: {test_log_file}")
        
        # Read and display the first few lines of the log file
        with open(test_log_file, "r") as f:
            first_lines = [next(f) for _ in range(10)]
            print("\nFirst 10 lines of log file:")
            for line in first_lines:
                print(line.strip())
    else:
        logger.error(f"Failed to create log file at: {test_log_file}")
    
    logger.info("Logging setup test completed")
