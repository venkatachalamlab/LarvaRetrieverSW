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
homographyFile = "homography.npy"
zHeightMapFile = "zHeightMap.npy"
imageFile = "TestImage.png"

instar = int(sys.argv[1])

margin = 50 # px
centerSize = 250 # px

# Dimensions and distances in millimeters
ZTravel = -10.
ZPickups = [0.5, 1.1, 1.7]
ZDropoffs = [0.7, 1.2, 1.7]

# Import homography
h = np.load(homographyFile)
hInv = np.linalg.inv(h)

# Import z height points and find plane equation for agar bed
measuredHeights = np.load(zHeightMapFile)

# Equation of a plane is a*x + b*y * c*z = d

# These three points are in the plane
p1 = measuredHeights[0]
p2 = measuredHeights[1]
p3 = measuredHeights[2]

# Therefore, these two vectors are in the plane
v1 = p3 - p1
v2 = p2 - p1

# The cross product is a vector normal to the plane
cp = np.cross(v1, v2)
a, b, c = cp

# This evaluates a * x3 + b * y3 + c * z3 which equals d
d = np.dot(cp, p3)

print('The equation is {0}x + {1}y + {2}z = {3}'.format(a, b, c, d))

# Create image masks. First is for finding larva in perimeter.
# Second is for finding space near the middle to replace larvae.

# Read in the image to get the size.
sampleImage = cv2.imread(imageFile, 0)
perimeterMask = np.zeros(sampleImage.shape, int)
centerMask = np.zeros(sampleImage.shape, int)
(h, w) = sampleImage.shape
perimeterMask[ 0:h, (w-h)/2:(w+h)/2 ] = 1
perimeterMask[ margin:h-margin, (w-h)/2+margin:(w+h)/2-margin ] = 0
perimeterIdx = (perimeterMask == 0)

centerMask[ (h-centerSize)/2:(h+centerSize)/2,
            (w-centerSize)/2:(w+centerSize)/2 ] = 1
centerIdx = (centerMask == 0)

# Define a few functions. Program continues below.

# To calculate the Z height of the agar bed at any X/Y coordinate:
# Use plane equation, solve for Z.
# z = (d - a*x - b*y)/c
def getZHeight(pt, a, b, c, d):
    x = pt[0]
    y = pt[1]
    if c == 0:
        return None
    return (d - a*x - b*y)/c

# Function to reposition larvae given:
#   source (np array, X & Y coordinates)
#   dest   (np array, X & Y coordinates)
#   instar (integer -- 1, 2 or 3)
def pickLarva(source, dest, z, instar):
    global ZTravel, ZPickups, ZDropoffs, robot
    assert (type(source) is numpy.ndarray and source.shape == (2L,) ), "source should be numpy array of shape (2L,)"
    assert (type(dest) is numpy.ndarray and dest.shape == (2L,) ), "dest should be numpy array of shape (2L,)"
    assert (instar == 1 or instar == 2 or instar == 3), "instar should be 1, 2 or 3"

    robot.sendSyncCmd("G01 F12000\n")
    robot.sendSyncCmd("G01 X{0} Y{1}\n".format(source[0], source[1]))
    robot.sendSyncCmd("G01 Z{0}\n".format(z+ZPickups[instar-1]))
    robot.sendSyncCmd("G04 P100\n")
    robot.sendSyncCmd("M42\n")
    robot.sendSyncCmd("G01 Z{0}\n".format(z+ZPickups[instar-1]+0.1))
    robot.sendSyncCmd("G04 P250\n")
    robot.sendSyncCmd("G01 F500 Z{0}\n".format(ZTravel))
    robot.sendSyncCmd("G01 F12000 X{0} Y{1}\n".format(dest[0], dest[1]))
    robot.sendSyncCmd("G01 F4000 Z{0}\n".format(z+ZDropoffs[instar-1]))
    robot.sendSyncCmd("M106\n")
    robot.sendSyncCmd("G04 P15\n")
    robot.sendSyncCmd("M43\n")
    robot.sendSyncCmd("M107\n")
    robot.sendSyncCmd("G04 P1000\n")
    robot.sendSyncCmd("G01 Z{0}\n".format(ZTravel))

def parseImage(img):
    larvaList = []
    kernel = np.array([[0, 1, 0],[1, 1, 1],[0, 1, 0]], dtype=uint8)
    # img is a masked image where the background
    # is black and larvae are white
    invImg = 255-img
    at = cv2.adaptiveThreshold(invImg, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 25)
    # Erode, then dilate to remove noise
    erodeImg = cv2.erode(at, kernel)
    clean = cv2.dilate()
    # Now find contours
    contours, h = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
            mmnts = cv2.moments(c)
            if ( 3 < mmnts['m00'] < 40 ):
                # Center of contour is m10/m00, m01/m00
                larvaList.append( np.array([ int(mmnts['m10'] / mmnts['m00'] ), int( mmnts['m01'] / mmnts['m00']) ], dtype=np.int16) )

    return larvaList

robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("G90\n")

prevTime = os.path.getmtime(imageFile)

while True:
    try:
        # Check file time
        if ( os.path.getmtime(imageFile) != prevTime ):
            # Load image from file as grayscale
            perimImage = cv2.imread(imageFile,0 )
            centerImage = latestImage.copy()
            # Apply masks
            perimImage[perimeterIdx] = 0
            centerImage[centerIdx] = 0
            # Parse image and move larvae (if necessary)
            larvaList = parseImage(perimImage)
            n = len(larvaList)
            larvaListRobot = cv2.perspectiveTransform(larvaList.reshape((n, 1, 2)), h).reshape((n, 2))
            for larva in larvaListRobot:
                zHeightAtLarva = getZHeight(larva, a, b, c, d)
                pickLarva(larva[0], larva[1], zHeightAtLarva, instar)
            robot.sendSyncCmd("G01 F12000 X0 Y0\n")
            robot.sendSyncCmd("M84\n")
        time.sleep(0.25)
    except KeyboardInterrupt:
        break

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("M84\n")
robot.close()
print "Exiting!"
time.sleep(3)
