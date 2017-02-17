# Copyright 2016, FlySorter LLC

import fsSerial
import os
import glob
import cv2
import numpy as np
import sys
import time

robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

robot.sendSyncCmd("G01 F8000\n")
robot.sendSyncCmd("G01 X50 Y50\n")
robot.sendSyncCmd("G01 Z-10\n")
robot.sendSyncCmd("M42\n")
robot.sendSyncCmd("G04 P150\n")
robot.sendSyncCmd("G01 Z-5\n")
robot.sendSyncCmd("G01 X20.5 Y20.5\n")
robot.sendSyncCmd("G01 Z-10\n")
robot.sendSyncCmd("M43\n") # Vacuum off
robot.sendSyncCmd("M44\n") # Air on
robot.sendSyncCmd("G04 P10\n")
robot.sendSyncCmd("M45\n") # Air off
robot.sendSyncCmd("G01 Z-5\n") # Return to Z travel height

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("M84\n")
robot.close()
