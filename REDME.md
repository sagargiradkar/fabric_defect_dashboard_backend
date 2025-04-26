# Fabric Defect Detection System

A comprehensive system for automated fabric quality control using computer vision and robotics. This system integrates camera input, deep learning-based defect detection, and robotic arm control to identify and sort fabric based on detected defects.

![System Overview](docs/images/system_overview.png)

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Module Explanations](#module-explanations)
- [Hardware Requirements](#hardware-requirements)
- [Development](#development)
- [License](#license)

## Features

- **Real-time Defect Detection**: Identifies fabric defects including holes, tears, stains, and stitching issues
- **Automated Sorting**: Controls a robotic arm to sort fabric into "defective" and "non-defective" categories
- **Flexible Operation Modes**:
  - GUI mode for interactive control and visualization
  - Headless mode for production environments
  - Simulation mode for testing without hardware
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Configurable Settings**: Adjustable parameters for detection sensitivity, camera settings, etc.

## System Architecture

The system follows a modular architecture with the following components:

```
fabric_defect_detection/
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration settings
├── lib/
│   ├── __init__.py
│   ├── camera.py          # Camera interface module
│   ├── detector.py        # Defect detection module
│   ├── robot_arm.py       # Robot arm control module
│   └── gui.py             # Graphical user interface
├── utils/
│   ├── __init__.py
│   └── logging_setup.py   # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_camera.py     # Camera module tests
│   ├── test_detector.py   # Detector module tests
│   ├── test_robot_arm.py  # Robot arm module tests
│   └── test_gui.py        # GUI module tests
├── main.py                # Main application entry point
└── requirements.txt       # Dependencies
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Raspberry Pi 4 (recommended) or similar platform
- Camera (Raspberry Pi Camera or USB camera)
- Servo-based robot arm
- YOLO model trained on fabric defects

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/fabric-defect-detection.git
   cd fabric-defect-detection
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download or train a YOLO model for fabric defect detection and place it in the `models` directory.

4. Configure the system by editing `config/settings.py` or using command-line arguments.

## Usage

### Running the Application

```bash
# Run with GUI (default)
python main.py

# Run in headless mode
python main.py --headless

# Run in simulation mode (no hardware required)
python main.py --simulation

# Run with custom model
python main.py --model path/to/model.pt

# Run system tests
python main.py --test
```

### Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `--headless` | Run in headless mode (no GUI) |
| `--simulation` | Run in simulation mode (no hardware required) |
| `--test` | Run system tests and exit |
| `--config PATH` | Path to custom configuration file |
| `--model PATH` | Path to custom detection model file |
| `--log-level LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--camera-width WIDTH` | Camera width in pixels |
| `--camera-height HEIGHT` | Camera height in pixels |
| `--confidence THRESHOLD` | Detection confidence threshold (0.0-1.0) |

## Module Explanations

### config/settings.py

This module contains all the configuration settings for the application, including:

- Camera settings (resolution, FPS)
- Detection model parameters and paths
- Robot arm position configurations
- GUI settings
- Logging configuration
- Processing parameters (confidence thresholds, intervals)

The settings are organized as class attributes with sensible defaults and can be overridden via command-line arguments or a custom configuration file.

### lib/camera.py

The camera module provides an interface to capture frames from a connected camera:

- **CameraModule**: Main class that handles camera initialization, frame capture, and resource management
- **Features**:
  - Automatic detection of available camera hardware
  - Graceful fallback to simulation mode
  - Performance metrics (FPS calculation)
  - Mock frame generation for testing

The module supports both Raspberry Pi Camera (via PiCamera2) and standard USB cameras (via OpenCV).

### lib/detector.py

The detector module is responsible for identifying defects in fabric images:

- **LiveFabricDefectDetector**: Main class that loads the YOLO model and performs detection
- **Features**:
  - Real-time defect detection using YOLOv8
  - Detection visualization
  - Confidence threshold filtering
  - Performance tracking (inference time)
  - Defect classification (holes, stitching issues, etc.)

The detector is designed to be efficient on resource-constrained devices like Raspberry Pi while maintaining reliable detection accuracy.

### lib/robot_arm.py

The robot arm module controls the physical robot arm for fabric handling:

- **RobotArmController**: Main class that manages servo movement and gripper operations
- **Features**:
  - Smooth servo movements with acceleration/deceleration
  - Position presets for home, pickup, and placement
  - Coordinated multi-servo movement using threads
  - Gripper control for fabric handling
  - Complete pick-and-place sequences
  - Emergency stop functionality
  - Comprehensive status reporting
  - Simulation mode for testing without hardware

The controller uses the Adafruit ServoKit library for hardware control and implements proper error handling for robust operation.

### lib/gui.py

The GUI module provides a user interface for interaction and visualization:

- **FabricDetectionGUI**: Main class that creates and manages the user interface
- **Features**:
  - Live video display with defect visualization
  - System status indicators
  - Manual and automatic control modes
  - Robot arm control buttons
  - Log display and event history
  - Emergency stop button
  - Performance metrics display

The GUI is built with Tkinter for cross-platform compatibility and is designed to be intuitive and informative.

### utils/logging_setup.py

The logging module configures comprehensive logging for the application:

- **setup_logging**: Main function that configures the logging infrastructure
- **Features**:
  - Console and file logging
  - Log rotation (prevents logs from growing too large)
  - Different formatting for console vs. file logs
  - Module-specific log levels
  - System information logging

This module ensures that all system events are properly recorded for monitoring and debugging.

### tests/

The tests directory contains comprehensive unit tests for all system components:

- **test_camera.py**: Tests for camera initialization, frame capture, and simulation
- **test_detector.py**: Tests for model loading, prediction, and visualization
- **test_robot_arm.py**: Tests for arm movement, gripper control, and sequence execution
- **test_gui.py**: Tests for UI components and interaction logic

Tests are implemented using pytest and include mocks for hardware components to enable testing without physical devices.

### main.py

The main entry point for the application:

- Parses command-line arguments
- Configures the application based on settings
- Initializes system components
- Runs the application in the requested mode (GUI, headless, tests)
- Handles exceptions and performs clean shutdown

## Hardware Requirements

### Recommended Hardware

- **Computer**: Raspberry Pi 4 (4GB+ RAM) or similar
- **Camera**: Raspberry Pi Camera Module V2 or compatible USB camera
- **Robot Arm**: 4-DOF servo-based arm with gripper
- **Power Supply**: 5V/3A for Raspberry Pi, separate power for servo motors
- **Display**: HDMI monitor (for GUI mode)

### Hardware Connections

- Camera connected via CSI (Raspberry Pi Camera) or USB
- Servo motors connected to PWM pins (or via I2C servo controller)
- Optional buttons/indicators connected to GPIO pins

## Development

### Running Tests

```bash
# Run all tests
python main.py --test

# Run specific test module
pytest tests/test_camera.py -v

# Run with coverage report
pytest --cov=lib tests/
```

### Adding New Features

1. Identify the module where your feature belongs
2. Implement your changes following the existing code style
3. Add appropriate tests in the tests/ directory
4. Update documentation to reflect your changes
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Note: This document provides an overview of the Fabric Defect Detection System. For detailed API documentation, please refer to the code docstrings and comments.* 