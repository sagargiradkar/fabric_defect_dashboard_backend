# tests/test_robot_arm.py
"""
Tests for the robot arm control module of the Fabric Defect Detection System.
"""

import pytest
import os
import sys
import time
import logging
import threading
from unittest.mock import MagicMock, patch

# Add parent directory to path to import from lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Settings
from utils.logging_setup import setup_logging

# Set up logging for tests
setup_logging(log_file=None, console_level=logging.WARNING)

# Mock ServoKit class
class MockServo:
    def __init__(self):
        self.angle = None
        self.actuation_range = None
        self.pulse_width_range = None
    
    def set_pulse_width_range(self, min_pulse, max_pulse):
        self.pulse_width_range = (min_pulse, max_pulse)

class MockServoKit:
    def __init__(self, channels=16):
        self.channels = channels
        self.servo = [MockServo() for _ in range(channels)]

# Test fixtures
@pytest.fixture
def servo_kit_mock():
    """Create a mock ServoKit for testing."""
    with patch('lib.robot_arm.ServoKit', new=MockServoKit):
        with patch('lib.robot_arm.SERVO_AVAILABLE', True):
            yield

@pytest.fixture
def robot_arm():
    """Create a robot arm controller in simulation mode for testing."""
    from lib.robot_arm import RobotArmController
    return RobotArmController(simulation_mode=True)

@pytest.fixture
def robot_arm_with_mock_hardware(servo_kit_mock):
    """Create a robot arm controller with mock hardware for testing."""
    from lib.robot_arm import RobotArmController
    return RobotArmController(simulation_mode=False)

# Tests
def test_robot_arm_init_simulation(robot_arm):
    """Test robot arm initialization in simulation mode."""
    assert robot_arm.simulation_mode == True
    assert robot_arm.arm_ready == True
    assert robot_arm.is_busy == False
    assert robot_arm.current_position == "home"

def test_robot_arm_init_hardware(robot_arm_with_mock_hardware):
    """Test robot arm initialization with mock hardware."""
    arm = robot_arm_with_mock_hardware
    assert arm.simulation_mode == False
    assert arm.arm_ready == True
    assert arm.is_busy == False
    assert arm.current_position == "home"
    
    # Check servo initialization
    for channel in range(4):  # First 4 channels should be initialized
        servo = arm.kit.servo[channel]
        if channel != arm.gripper_channel:
            assert servo.actuation_range == 180
            assert servo.pulse_width_range == (500, 2500)

def test_robot_arm_positions(robot_arm):
    """Test that the robot arm has the expected positions."""
    assert "home" in robot_arm.positions
    assert "pickup" in robot_arm.positions
    assert "defective" in robot_arm.positions
    assert "non_defective" in robot_arm.positions

def test_robot_arm_move_simulation(robot_arm):
    """Test moving the robot arm in simulation mode."""
    # Should not raise an exception
    robot_arm.move_to_position(robot_arm.positions["home"])
    robot_arm.move_to_position(robot_arm.positions["pickup"])
    robot_arm.move_to_position(robot_arm.positions["defective"])
    robot_arm.move_to_position(robot_arm.positions["non_defective"])

def test_robot_arm_move_hardware(robot_arm_with_mock_hardware):
    """Test moving the robot arm with mock hardware."""
    arm = robot_arm_with_mock_hardware
    
    # Move to home position
    arm.move_to_position(arm.positions["home"])
    
    # Check that servos were moved
    for channel, angle in arm.positions["home"].items():
        if channel != arm.gripper_channel:
            assert arm.kit.servo[channel].angle == angle

def test_robot_arm_gripper(robot_arm_with_mock_hardware):
    """Test gripper open and close with mock hardware."""
    arm = robot_arm_with_mock_hardware
    
    # Open gripper
    arm.gripper_open()
    assert arm.kit.servo[arm.gripper_channel].angle == 0
    
    # Close gripper
    arm.gripper_close()
    assert arm.kit.servo[arm.gripper_channel].angle == 180

def test_robot_arm_handle_object(robot_arm):
    """Test complete object handling sequence."""
    # Test handling defective item
    robot_arm.handle_object(defective=True)
    assert robot_arm.is_busy == False
    assert robot_arm.current_position == "home"
    
    # Test handling good item
    robot_arm.handle_object(defective=False)
    assert robot_arm.is_busy == False
    assert robot_arm.current_position == "home"

def test_robot_arm_emergency_stop(robot_arm_with_mock_hardware):
    """Test emergency stop functionality."""
    arm = robot_arm_with_mock_hardware
    
    # Start a handling sequence in a thread
    def handle_task():
        arm.handle_object(defective=True)
    
    thread = threading.Thread(target=handle_task)
    thread.start()
    
    # Brief delay to ensure thread starts
    time.sleep(0.1)
    
    # Trigger emergency stop
    arm.emergency_stop()
    
    # Wait for thread to complete
    thread.join(timeout=1.0)
    
    # Check that busy flag was reset
    assert arm.is_busy == False

def test_robot_arm_get_status(robot_arm):
    """Test getting robot arm status."""
    status = robot_arm.get_status()
    
    assert 'ready' in status
    assert 'busy' in status
    assert 'simulation' in status
    assert 'position' in status
    assert 'last_action' in status
    assert 'gripper' in status
    
    assert status['ready'] == True
    assert status['busy'] == False
    assert status['simulation'] == True
    assert status['position'] == "home"
    assert status['gripper'] == "closed"  # Default is closed

def test_robot_arm_smooth_move(robot_arm_with_mock_hardware):
    """Test smooth servo movement with easing function."""
    arm = robot_arm_with_mock_hardware
    servo = arm.kit.servo[0]
    
    # Set initial position
    servo.angle = 0
    
    # Move to new position
    arm.smooth_move(servo, 180, steps=5, delay=0.01)
    
    # Check final position
    assert servo.angle == 180

def test_robot_arm_coordinated_movement(robot_arm_with_mock_hardware):
    """Test coordinated movement of arm and gripper."""
    arm = robot_arm_with_mock_hardware
    
    # Set initial gripper position
    arm.kit.servo[arm.gripper_channel].angle = 180
    
    # Test moving to position while opening gripper
    test_position = {0: 45, 1: 90, 2: 135}
    arm.move_to_position_with_gripper(test_position, 180, 0, steps=3, delay=0.01)
    
    # Check final positions
    for channel, angle in test_position.items():
        assert arm.kit.servo[channel].angle == angle
    
    assert arm.kit.servo[arm.gripper_channel].angle == 0

def test_exception_handling(robot_arm_with_mock_hardware):
    """Test exception handling during robot arm operations."""
    arm = robot_arm_with_mock_hardware
    
    # Make servo movement raise an exception
    arm.kit.servo[0].set_pulse_width_range = MagicMock(side_effect=Exception("Test exception"))
    
    # Should not raise an exception to caller
    arm._initialize_servos()  # This will trigger the exception internally
    
    # Handle object should also handle exceptions
    arm.handle_object(defective=True)
    
    # Should still reset busy flag
    assert arm.is_busy == False

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
