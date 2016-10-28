# Copyright 2016, FlySorter LLC

import fsSerial
import os
import glob
import cv2
import numpy as np
import sys

# General structure of this program:
#
# 1. Initialize serial port to communicate with SmoothieBoard
# 2. Read in config information for transformation between
#    image coordinates and robot coordinates, and also Z heights.
# 3. Watch for change in designated image file
# 4. When change occurs:
#       a. Open image file
#       b. Find larva(e) around perimeter of agar bed
#       c. If found:
#           i. Find open space(s) near center of agar bed
#           ii. Direct robot to reposition larva(e)
#           iii. Move robot out of view
# Ongoing - listen for interrupt; quit cleanly.

if ( len(sys.argv) != 2 ) or ( int(sys.argv[1]) < 1 ) or ( int(sys.argv[1]) > 3 ):
    print "Usage: {0} N".format(sys.argv[0])
    print "Where N is the size/age of the larvae -- 1, 2, or 3"
    exit()
    
# Configuration parameters

COMPort = "COM3"
homographyFile = ""
imageFile = "TestImage.png"
instar = int(sys.argv[1])

ZTravel = -10.
ZPickups = [ -22.1, -21.5, -20.9 ]
ZDropoffs = [ -21.9, -21.6, -21.3 ]

# Function to reposition larvae given:
#   source (np array, X & Y coordinates)
#   dest   (np array, X & Y coordinates)
#   instar (integer -- 1, 2 or 3)
def pickLarva(source, dest, instar):
    global ZTravel, ZPickups, ZDropoffs, robot
    assert (type(source) is numpy.ndarray and source.shape == (2L,) ), "source should be numpy array of shape (2L,)"
    assert (type(dest) is numpy.ndarray and dest.shape == (2L,) ), "dest should be numpy array of shape (2L,)"
    assert (instar == 1 or instar == 2 or instar == 3), "instar should be 1, 2 or 3"
    
    robot.sendSyncCmd("G01 F12000\n")
    robot.sendSyncCmd("G01 X{0} Y{1}\n".format(source[0], source[1]))
    robot.sendSyncCmd("G01 Z{0}\n".format(ZPickups[instar-1]))
    robot.sendSyncCmd("G04 P100\n")
    robot.sendSyncCmd("M42\n")
    robot.sendSyncCmd("G01 Z{0}\n".format(ZPickups[instar-1]+0.1))
    robot.sendSyncCmd("G04 P250\n")
    robot.sendSyncCmd("G01 F500 Z{0}\n".format(ZTravel))
    robot.sendSyncCmd("G01 F12000 X{0} Y{1}\n".format(dest[0], dest[1]))
    robot.sendSyncCmd("G01 F4000 Z{0}\n".format(ZDropoffs[instar-1]))
    robot.sendSyncCmd("M106\n")
    robot.sendSyncCmd("G04 P15\n")
    robot.sendSyncCmd("M43\n")
    robot.sendSyncCmd("M107\n")
    robot.sendSyncCmd("G04 P1000\n")
    robot.sendSyncCmd("G01 Z{0}\n".format(ZTravel))


def parseImage(img):
    larvaList = []
    return larvaList

robot = fsSerial.fsSerial(COMPort, baud = 115200)
robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("G90\n")

prevTime = os.path.getmtime(imageFile)

while True:
    try:
        # Check file time
        if ( os.path.getmtime(imageFile) != prevTime ):
            # Load image from file
            latestImage = cv2.imread(imageFile)
            # Parse image and move larvae (if necessary)
            larvaList = parseImage(latestImage)
            for larva in larvaList:
                pickLarva(larva[0], larva[1], instar)
            robot.sendSyncCmd("G01 F12000 X0 Y0\n")
            robot.sendSyncCmd("M84\n")
        time.sleep(0.25)
    except KeyboardInterrupt:
        print "Exiting!"
        time.sleep(3)
        exit()
        

robot.close()
