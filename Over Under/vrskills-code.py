# VEXcode Generated Robot Configuration
import math
import random
from vexcode_vrc import *
from vexcode_vrc.events import get_Task_func

# Brain should be defined by default
brain = Brain()

drivetrain = Drivetrain("drivetrain", 0)
arm_motor = Motor("ArmMotor", 3)
rotation = Rotation("Rotation", 7)
intake_motor = Motor("IntakeMotor", 8)
optical = Optical("Optical", 11)
gps = GPS("GPS", 20)


# endregion VEXcode Generated Robot Configuration

# 2055A Virtual Skills Code
# -----------------------------------
# Author(s): Edison
# Purpose:
# Started: 01/06/2024
# Updated: 01/06/2024
# -----------------------------------

class Chassis():
    def __init__(self):
        pass

    def logPose(self):
        brain.screen.print("Angle: " + str(gps.heading()))
        return

    def moveTo(self, x, y, theta):
        return


def raise_arm():
    return


def ram(timeout, forwards=True):
    """
    INCLUDE FUNCTION COMMENTS
    """
    drivetrain.set_drive_velocity(50, PERCENT)
    if forwards:
        drivetrain.drive(FORWARD)
    else:
        drivetrain.drive(REVERSE)
    wait(timeout, SECONDS)
    drivetrain.stop()
    return


def alliance_triballs():
    """
    INCLUDE FUNCTION COMMENTS
    """
    # Turn to score alliance triballs
    drivetrain.turn_to_heading(115, DEGREES)
    drivetrain.set_drive_velocity(80, PERCENT)

    drivetrain.drive_for(REVERSE, 19, INCHES)
    drivetrain.turn_to_heading(180, DEGREES)

    ram(2, False)

    drivetrain.drive_for(FORWARD, 10, INCHES)
    drivetrain.turn_to_heading(180, DEGREES)

    # Rams into blue net while scoring preloaded triball
    intake_motor.spin(REVERSE)
    wait(2, SECONDS);
    intake_motor.stop()
    return


def main():
    chassis = Chassis()
    brain.screen.print("HELLO")
    # chassis.logPose()
    wait(20, MSEC)
    return


vr_thread(main)
