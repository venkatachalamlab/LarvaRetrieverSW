# Copyright 2016, FlySorter LLC

import fsSerial
import os
import glob
import cv2
import numpy as np
import sys
import time

from LPConstants import *

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

#if ( len(sys.argv) != 2 ) or ( int(sys.argv[1]) < 1 ) or ( int(sys.argv[1]) > 3 ):
#    print "Usage: {0} N".format(sys.argv[0])
#    print "Where N is the size/age of the larvae -- 1, 2, or 3"
#    exit()

#instar = int(sys.argv[1])
instar = 2

# Check that files exist
if ( os.path.isfile(homographyFile) is False ) or \
   ( os.path.isfile(zHeightMapFile) is False ) or \
   ( os.path.isfile(imageFile)      is False ):
    print "Could not file calibration files or image file."
    print "[", homographyFile, zHeightMapFile, imageFile, "]"
    exit()

# Import homography
H = np.load(homographyFile)
HInv = np.linalg.inv(H)

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

#

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
def pickLarva(source, dest, instar):
    global ZTravel, ZPickups, ZDropoffs, robot, a, b, c, d
    assert (type(source) is np.ndarray and source.shape == (2L,) ), "source should be numpy array of shape (2L,)"
    assert (type(dest) is np.ndarray and dest.shape == (2L,) ), "dest should be numpy array of shape (2L,)"
    assert (instar == 1 or instar == 2 or instar == 3), "instar should be 1, 2 or 3"

    zHeightAtLarva = getZHeight(source, a, b, c, d)
    print "zHeightAtLarva:", zHeightAtLarva
    zDropoffHeight = getZHeight(dest, a, b, c, d)
    print "zDropoffHeight:", zDropoffHeight
    robot.sendSyncCmd("G01 F10000\n")
    robot.sendSyncCmd("G01 X{0} Y{1}\n".format(source[0], source[1]))
    robot.sendSyncCmd("G01 F2000 Z{0}\n".format(zHeightAtLarva+ZPickups[instar-1]))
    robot.sendSyncCmd("M42\n")
    robot.sendSyncCmd("G01 F2000 Z{0}\n".format(zHeightAtLarva+ZPickups[instar-1]+0.1))
    robot.sendSyncCmd("G04 P150\n")
    robot.sendSyncCmd("G01 F2000 Z{0}\n".format(ZTravel))
    robot.sendSyncCmd("G01 F10000 X{0} Y{1}\n".format(dest[0], dest[1]))
    robot.sendSyncCmd("G01 F2000 Z{0}\n".format(zDropoffHeight+ZDropoffs[instar-1]))
    robot.sendSyncCmd("M43\n") # Vacuum off
    robot.sendSyncCmd("M44\n") # Air on
    robot.sendSyncCmd("G04 P50\n") # Pause for 50 ms
    robot.sendSyncCmd("M45\n") # Air off
    robot.sendSyncCmd("G01 F2000 Z{0}\n".format(ZTravel)) # Return to Z travel height


def parseImage(img):
    larvaList = []
    kernel = np.array([[0, 1, 0],[1, 1, 1],[0, 1, 0]], dtype=np.uint8)
    # img is a masked image where the background
    # is black and larvae are white
    invImg = 255-img
    at = cv2.adaptiveThreshold(invImg, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 55, 25)
    #cv2.imwrite("threshold.png", at)
    # Erode, then dilate to remove noise
    erodeImg = cv2.erode(at, kernel)
    clean = cv2.dilate(erodeImg, kernel)
    cv2.imwrite("clean.png", erodeImg)
    # Now find contours
    contours, h = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
            mmnts = cv2.moments(c)
            if ( mmnts['m00'] != 0 ):
                #print " mmnts['m00']:", mmnts['m00'], " at ", (mmnts['m10'] / mmnts['m00'] ), ( mmnts['m01'] / mmnts['m00'])
                if ( larvaRanges[instar-1][0] < mmnts['m00'] < larvaRanges[instar-1][1] ):
                    # Center of contour is m10/m00, m01/m00
                    print "Larva size:", mmnts['m00']
                    larvaList.append( np.array([ (mmnts['m10'] / mmnts['m00'] ), ( mmnts['m01'] / mmnts['m00']) ], dtype=np.int16) )

    return larvaList

def findSpace(img):
    global centerSize, w, h
    destinations = []
    kernel = np.array([[0, 1, 0],[1, 1, 1],[0, 1, 0]], dtype=np.uint8)
    # img is a masked image where the background
    # is black and larvae are white
    invImg = 255-img
    at = cv2.adaptiveThreshold(invImg, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 55, 25)
    # Erode, then dilate to remove noise
    erodeImg = cv2.erode(at, kernel)
    clean = cv2.dilate(erodeImg, kernel)
    #cv2.imwrite("clean.png", erodeImg)
    # Divide center into 50 px (approx. 7mm) squares
    # If *any* pixel within each square is white, the square is
    # considered "not empty".
    # Return a list of the center points of all empty squares.
    for x in range(centerSize/50):
        for y in range(centerSize/50):
            if (not np.any(clean[ (h-centerSize)/2+y*50:(h-centerSize)/2+(y+1)*50,
                       (w-centerSize)/2+x*50:(w-centerSize)/2+(x+1)*50]) ):
                destinations.append(np.array([(w-centerSize)/2+x*50+25,
                                              (h-centerSize)/2+y*50+25], dtype=np.int16))
            clean[ margin:h-margin, (w-h)/2+margin:(w+h)/2-margin ]
    return destinations

robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("G90\n")

robot.sendSyncCmd("M42\n")
time.sleep(1)

pString = robot.sendCmdGetReply("M105\n")
robot.sendSyncCmd("M43\n")
p = float(pString.split(' ')[1].split(':')[1])
if p < minVacReading:
    print "Low pressure reading (", p, "). Is the pump on/stopcock open?"
    robot.close()
    exit()

prevTime = os.path.getmtime(imageFile)

print "Checking image file time."

while True:
    try:
        # Check file time
        if ( os.path.getmtime(imageFile) != prevTime ):
            print "Updated @", time.time()
            # Load image from file as grayscale
            perimImage = cv2.imread(imageFile,0 )
            if perimImage is not None:

                centerImage = perimImage.copy()
                # Apply masks
                perimImage[perimeterIdx] = 0
                centerImage[centerIdx] = 0
                #cv2.imwrite("mask.png", perimImage)
                # Parse image and move larvae (if necessary)
                larvaList = parseImage(perimImage)
                destList = findSpace(centerImage)
                if ( len(larvaList) > len(destList) ):
                    print "Error: more flies than destination squares."
                    for i in range(len(larvaList)-len(destList)+1):
                        destList.append(np.array([int(centerImage.shape[1]/2), int(centerImage.shape[0]/2)], float))
                n = len(larvaList)
                print "Found", n, "larva."
                destCount = 0
                if n > 0:
                    larvaListRobot = cv2.perspectiveTransform(np.asarray(larvaList, float).reshape((1, n, 2)), H).reshape((n, 2))
                    destListRobot = cv2.perspectiveTransform(np.asarray(destList, float).reshape((1, len(destList), 2)), H).reshape((len(destList), 2))
                    for n in range(n):
                        larva = larvaListRobot[n]
                        print "Larva location (image coords):", larvaList[n]
                        print "Larva location (robot coords):", larva
                        if ( larva[0] < 0 ) or ( larva[1] < 0 ) or \
                           ( larva[0] > 250 ) or ( larva[1] > 220 ):
                            print "Robot coordinate out-of-bounds. Skipping."
                        else:
                            pickLarva(larva, destListRobot[destCount], instar)
                        destCount += 1
                    robot.sendSyncCmd("G01 F10000 X0 Y0\n")
                prevTime = os.path.getmtime(imageFile)

        time.sleep(0.25)
    except KeyboardInterrupt:
        break

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("M84\n")
robot.close()
print "Exiting! Don't for get to turn off the air!"
time.sleep(3)
