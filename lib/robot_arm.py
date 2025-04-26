# lib/robot_arm.py
"""
Robot arm control module for the Fabric Defect Detection System.

This module manages the robot arm's movement and gripper operations for
picking up and placing fabric based on defect detection results.
"""

import logging
import time
import threading
import traceback
from config.settings import Settings

# Try to import ServoKit, but gracefully handle if not available
try:
    from adafruit_servokit import ServoKit

    SERVO_AVAILABLE = True
except ImportError:
    SERVO_AVAILABLE = False
    logging.getLogger("fabric_detection.robot_arm").warning(
        "ServoKit not available - robot arm functionality will be simulated"
    )


class RobotArmController:
    """
    Robot arm controller for fabric handling

    Controls the robot arm's movement and gripper operations for picking up and
    placing fabric based on defect detection.
    """

    def __init__(self, simulation_mode=None, arm_positions=None):
        """
        Initialize the robot arm controller

        Args:
            simulation_mode: Force simulation mode (optional)
            arm_positions: Dictionary of arm positions (optional)
        """
        self.logger = logging.getLogger("fabric_detection.robot_arm")

        # Set simulation mode based on ServoKit availability
        self.simulation_mode = (
            simulation_mode if simulation_mode is not None else not SERVO_AVAILABLE
        )
        self.arm_ready = False

        # Initialize state variables
        self.is_busy = False
        self.last_action_time = 0
        self.current_position = "unknown"

        # Initialize arm positions
        self.positions = arm_positions or Settings.ARM_POSITIONS

        try:
            if self.simulation_mode:
                self.logger.warning(
                    "Running in simulation mode - no actual servo control"
                )
                self.arm_ready = True
                self.current_position = "home"  # Assume we start at home in simulation
            else:
                self.logger.debug("Initializing robot arm controller...")
                self.kit = ServoKit(channels=16)
                self.gripper_channel = Settings.GRIPPER_CHANNEL

                # Initialize the gripper servo
                self.logger.debug(
                    f"Setting up gripper on channel {self.gripper_channel}"
                )
                # Configure servo for the gripper range
                self.kit.servo[self.gripper_channel].actuation_range = 180
                self.kit.servo[self.gripper_channel].set_pulse_width_range(500, 2500)

                # Initialize arm position
                self._initialize_servos()
                self.move_to_position(self.positions["home"])
                self.current_position = "home"

                # Start with gripper closed
                self.gripper_close()

            self.logger.info("Robot arm initialized successfully")
            self.arm_ready = True

        except Exception as e:
            self.logger.error(f"Failed to initialize robot arm: {e}")
            traceback.print_exc()
            self.arm_ready = False
            self.simulation_mode = True

    def _initialize_servos(self):
        """Initialize all servo channels with proper configuration"""
        if self.simulation_mode:
            return

        try:
            # Configure each servo used in the arm
            for channel in range(4):  # Assuming channels 0-3 are used
                self.logger.debug(f"Configuring servo channel {channel}")
                self.kit.servo[channel].actuation_range = 180
                self.kit.servo[channel].set_pulse_width_range(500, 2500)

                # Move to middle position initially to avoid sudden movements
                if channel != self.gripper_channel:
                    self.kit.servo[channel].angle = 90
                    time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error initializing servos: {e}")
            raise

    def smooth_move(self, servo, target_angle, steps=None, delay=None):
        """
        Move a servo smoothly from current position to target angle using easing function

        Args:
            servo: The servo to move
            target_angle: Target angle to move to
            steps: Number of steps for smooth motion
            delay: Delay between steps
        """
        steps = steps or Settings.MOVEMENT_STEPS
        delay = delay or Settings.MOVEMENT_DELAY

        if self.simulation_mode:
            self.logger.info(f"SIM: Moving servo to {target_angle}")
            time.sleep(0.1)  # Simulate movement time
            return

        current_angle = servo.angle if servo.angle is not None else 0
        current_angle = max(0, min(current_angle, 180))
        target_angle = max(0, min(target_angle, 180))
        delta = target_angle - current_angle

        # Skip if no movement needed
        if abs(delta) < 1:
            return

        for step in range(1, steps + 1):
            t = step / steps
            # Quadratic easing for smooth acceleration/deceleration
            eased_t = 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t
            angle = current_angle + delta * eased_t
            servo.angle = angle
            time.sleep(delay)

        servo.angle = target_angle

    def move_to_position(self, position_dict, steps=None, delay=None):
        """
        Move all servos to specified position in parallel threads

        Args:
            position_dict: Dictionary mapping servo channels to target angles
            steps: Number of steps for smooth motion
            delay: Delay between steps
        """
        steps = steps or Settings.MOVEMENT_STEPS
        delay = delay or Settings.MOVEMENT_DELAY

        if self.simulation_mode:
            self.logger.info(f"SIM: Moving to position {position_dict}")
            time.sleep(0.5)  # Simulate movement time
            return

        threads = []
        for channel, angle in position_dict.items():
            if (
                channel != self.gripper_channel
            ):  # Don't include gripper in position movements
                thread = threading.Thread(
                    target=self.smooth_move,
                    args=(self.kit.servo[channel], angle, steps, delay),
                )
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

    def move_to_position_with_gripper(
        self,
        position_dict,
        start_gripper_angle,
        end_gripper_angle,
        steps=None,
        delay=None,
    ):
        """
        Move arm to position while simultaneously transitioning gripper

        Args:
            position_dict: Dictionary mapping servo channels to target angles
            start_gripper_angle: Starting gripper angle
            end_gripper_angle: Ending gripper angle
            steps: Number of steps for smooth motion
            delay: Delay between steps
        """
        steps = steps or Settings.MOVEMENT_STEPS
        delay = delay or Settings.MOVEMENT_DELAY

        if self.simulation_mode:
            self.logger.info(
                f"SIM: Moving to position with gripper {start_gripper_angle}->{end_gripper_angle}"
            )
            time.sleep(0.5)  # Simulate movement time
            return

        try:
            # Start arm movement threads
            arm_threads = []
            for channel, angle in position_dict.items():
                if channel != self.gripper_channel:
                    thread = threading.Thread(
                        target=self.smooth_move,
                        args=(self.kit.servo[channel], angle, steps, delay),
                    )
                    arm_threads.append(thread)
                    thread.start()

            # Start gripper movement in parallel (if needed)
            if (
                abs(start_gripper_angle - end_gripper_angle) > 5
            ):  # Only move if significant change
                gripper_servo = self.kit.servo[self.gripper_channel]

                # Calculate intermediate points for the gripper
                for step in range(1, steps + 1):
                    t = step / steps
                    # Quadratic easing
                    eased_t = 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t
                    gripper_angle = (
                        start_gripper_angle
                        + (end_gripper_angle - start_gripper_angle) * eased_t
                    )
                    gripper_servo.angle = gripper_angle
                    time.sleep(delay)

                # Ensure final position is exact
                gripper_servo.angle = end_gripper_angle

            # Wait for arm movements to complete
            for thread in arm_threads:
                thread.join()

        except Exception as e:
            self.logger.error(f"Error in coordinated movement: {e}")
            traceback.print_exc()

    def gripper_open(self):
        """Open the gripper by setting servo to 0 degrees"""
        self.logger.info("Gripper Opening...")
        if self.simulation_mode:
            self.logger.info("SIM: Gripper opened")
            time.sleep(0.5)
            return

        try:
            # Set gripper to open position
            self.kit.servo[self.gripper_channel].angle = 0
            self.logger.debug(f"Set gripper angle to 0")
            time.sleep(1.0)  # Allow time for the gripper to fully open
        except Exception as e:
            self.logger.error(f"Error opening gripper: {e}")
            traceback.print_exc()

    def gripper_close(self):
        """Close the gripper by setting servo to 180 degrees"""
        self.logger.info("Gripper Closing...")
        if self.simulation_mode:
            self.logger.info("SIM: Gripper closed")
            time.sleep(0.5)
            return

        try:
            # Set gripper to closed position
            self.kit.servo[self.gripper_channel].angle = 180
            self.logger.debug(f"Set gripper angle to 180")
            time.sleep(1.0)  # Allow time for the gripper to fully close
        except Exception as e:
            self.logger.error(f"Error closing gripper: {e}")
            traceback.print_exc()

    def get_gripper_angle(self):
        """Get current gripper angle, or 180 (closed) in simulation mode"""
        if self.simulation_mode:
            return 180
        return self.kit.servo[self.gripper_channel].angle or 180

    def handle_object(self, defective=True):
        """
        Complete pick-and-place sequence for fabric handling

        Args:
            defective: Whether the object is defective (determines placement location)
        """
        self.is_busy = True

        try:
            # Define our positions
            home_position = self.positions["home"]
            pick_position = self.positions["pickup"]

            # Select place position based on defective status
            if defective:
                place_position = self.positions["defective"]
                self.logger.info("Handling defective item")
            else:
                place_position = self.positions["non_defective"]
                self.logger.info("Handling good item")

            # 1. Move from home position to pick position while opening gripper
            self.logger.info("-> Moving to pick position while opening gripper")
            self.move_to_position_with_gripper(pick_position, 180, 0)
            self.current_position = "pickup"
            time.sleep(0.5)  # Short pause

            # 2. Close gripper to pick the object
            self.logger.info("-> Closing gripper to grasp object")
            self.gripper_close()
            time.sleep(0.5)

            # 3. Move up first to avoid dragging fabric
            self.logger.info("-> Moving up with object")
            intermediate_position = {0: pick_position[0], 1: 45, 2: 45}
            self.move_to_position(intermediate_position)
            time.sleep(0.5)

            # 4. Move to place position with closed gripper
            self.logger.info("-> Moving to place position")
            # First move horizontally to position
            horizontal_position = {0: place_position[0], 1: 45, 2: 45}
            self.move_to_position(horizontal_position)
            time.sleep(0.5)

            # Then move down to release height
            release_position = {
                0: place_position[0],
                1: place_position[1],
                2: place_position[2],
            }
            self.move_to_position(release_position)
            self.current_position = "defective" if defective else "non_defective"
            time.sleep(0.5)

            # 5. Open gripper to release the object
            self.logger.info("-> Opening gripper to release object")
            self.gripper_open()
            time.sleep(0.5)

            # 6. Move back to home position while closing gripper
            self.logger.info("-> Returning to home position while closing gripper")
            # First move up at current position
            up_position = {0: place_position[0], 1: 45, 2: 45}
            self.move_to_position(up_position)
            time.sleep(0.5)

            # Then move back to home while closing gripper
            self.move_to_position_with_gripper(home_position, 0, 180)
            self.current_position = "home"

            self.logger.info("-> Object handling sequence complete")

        except Exception as e:
            self.logger.error(f"Error in robot movement sequence: {e}")
            traceback.print_exc()
        finally:
            self.is_busy = False
            self.last_action_time = time.time()

    def emergency_stop(self):
        """Emergency stop - immediately halt all movement"""
        self.logger.warning("EMERGENCY STOP TRIGGERED")

        if not self.simulation_mode:
            try:
                # Stop all servos by setting them to their current position
                for channel in range(4):  # Assuming 4 channels
                    if (
                        hasattr(self.kit.servo[channel], "angle")
                        and self.kit.servo[channel].angle is not None
                    ):
                        current_angle = self.kit.servo[channel].angle
                        self.kit.servo[channel].angle = current_angle
            except Exception as e:
                self.logger.error(f"Error during emergency stop: {e}")

        # Reset state
        self.is_busy = False

    def get_status(self):
        """
        Get the current status of the robot arm

        Returns:
            dict: Status information including current position, busy state, etc.
        """
        return {
            "ready": self.arm_ready,
            "busy": self.is_busy,
            "simulation": self.simulation_mode,
            "position": self.current_position,
            "last_action": self.last_action_time,
            "gripper": "open" if self.get_gripper_angle() < 90 else "closed",
        }


# Test code for standalone testing
if __name__ == "__main__":
    # Set up basic logging to console
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    logger = logging.getLogger("robot_arm_test")
    logger.info("Testing Robot Arm Controller")

    # Create robot arm controller (will auto-detect if hardware is available)
    arm = RobotArmController()

    # Print initial status
    status = arm.get_status()
    logger.info(f"Initial status: {status}")

    if not arm.arm_ready:
        logger.error("Robot arm not ready, test aborted")
        exit(1)

    try:
        # Test basic movements
        logger.info("==== Testing Basic Movements ====")

        # Test gripper
        logger.info("Testing gripper open")
        arm.gripper_open()
        time.sleep(1)

        logger.info("Testing gripper close")
        arm.gripper_close()
        time.sleep(1)

        # Test positions
        logger.info("Testing home position")
        arm.move_to_position(arm.positions["home"])
        time.sleep(1)

        logger.info("Testing pickup position")
        arm.move_to_position(arm.positions["pickup"])
        time.sleep(1)

        logger.info("Testing defective position")
        arm.move_to_position(arm.positions["defective"])
        time.sleep(1)

        logger.info("Testing non-defective position")
        arm.move_to_position(arm.positions["non_defective"])
        time.sleep(1)

        logger.info("Returning to home")
        arm.move_to_position(arm.positions["home"])
        time.sleep(1)

        # Test pick and place sequences
        logger.info("==== Testing Pick and Place Sequences ====")

        logger.info("Testing defective handling sequence")
        arm.handle_object(defective=True)
        time.sleep(1)

        logger.info("Testing good item handling sequence")
        arm.handle_object(defective=False)
        time.sleep(1)

        # Test emergency stop
        logger.info("==== Testing Emergency Stop ====")
        logger.info("Starting movement...")

        def move_arm():
            arm.handle_object(defective=True)

        # Start movement in a thread
        thread = threading.Thread(target=move_arm)
        thread.start()

        # Let it run for a second
        time.sleep(1)

        # Trigger emergency stop
        logger.info("Triggering emergency stop!")
        arm.emergency_stop()

        # Wait for the thread to complete
        thread.join()

        # Final status
        status = arm.get_status()
        logger.info(f"Final status: {status}")

        logger.info("Robot arm test completed successfully")

    except Exception as e:
        logger.error(f"Error during robot arm test: {e}")
        traceback.print_exc()
    finally:
        # Return to home position and close gripper
        if arm.arm_ready:
            logger.info("Returning to home position")
            arm.move_to_position(arm.positions["home"])
            arm.gripper_close()
