# Copyright 2016, FlySorter LLC

import fsSerial
import numpy as np
import cv2
import time

from LPConstants import *

# Outline of camera calibration steps:
# 0. Use pylon viewer to set exposure, gain, etc.
# 1. Direct robot to move to 4 points.
# 2. At each point, direct user to attach calibration disc
# 3. When pressure sensor detects disc attached, drop it on agar bed.
# 4. Capture image with camera
# 5. Detect location of calibration points within image.
# 6. Create homography transformation from points.
# 7. Output homography matrix to config file.

robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

circlePointsRobot = np.array( [[45.0, 25.0],
                              [170.0, 35.0],
                              [185.0, 175.0],
                              [30.0, 190.0]])

colorList = [ (255, 0, 0),
              (0, 255, 0),
              (0, 0, 255),
              (255, 255, 0) ]

zHeight = -15.
transitSpeed = 6000

# Home robot, set to absolute coords
robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("G90\n")

for pt in circlePointsRobot:
    robot.sendSyncCmd("G01 F{0}\n".format(transitSpeed))
    robot.sendSyncCmd("G01 X{0} Y{1}\n".format(pt[0], pt[1]))
    robot.sendSyncCmd("G01 F2000 Z{0}\n".format(-2))
    robot.sendSyncCmd("M42\n")
    print "Attach disc."
    count=0
    pc=0
    p = 35.
    while ( count < 100 ) and ( pc < 2 ):
        pString = robot.sendCmdGetReply("M105\n")
        p = float(pString.split(' ')[1].split(':')[1])
        if ( p >= 50 ):
            print "Pressure:", p
            pc += 1
        time.sleep(0.1)
        count += 1
    if ( count >= 100 ):
        print "Timed out."
        robot.sendSyncCmd("M43\n")
    else:
        time.sleep(2)
        robot.sendSyncCmd("G01 Z{0}\n".format(zHeight))
        robot.sendSyncCmd("G04 P500\n")
        robot.sendSyncCmd("M43\n")
        robot.sendSyncCmd("M44\n")
        robot.sendSyncCmd("G01 Z{0}\n".format(zHeight+0.1))
        robot.sendSyncCmd("G04 P50\n")
        robot.sendSyncCmd("M45\n")
        robot.sendSyncCmd("G01 Z{0}\n".format(-2))

# Now image has been placed. Get robot out of the camera's view
robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("M84\n")

# Done with the robot, for now.
robot.close()

print "Robot closed. Opening camera."


# Open the camera
# May need to edit the index to match your system, since it depends
# on how many cameras there are and in what order they enumerate.
webcam = cv2.VideoCapture(2)

print "Camera open, setting params."

# Set the w/h
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 2592)
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 1944)

print "Params set, grabbing image."

# Grab an image and flip it around
res, img = webcam.read()

webcam.release()

# Find circles
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blur = cv2.medianBlur(gray, 5)
circles = cv2.HoughCircles(blur, cv2.cv.CV_HOUGH_GRADIENT, 1.3, 100,
                           minRadius=25, maxRadius=150)

circlePointsImage = np.zeros((4, 2))

if circles is None:
    print "No circles found."
else:
    icircles = np.round(circles[0, :]).astype("int")
    c = circles.astype(float)[0]
    print "Circles found:", c
    # Sort the circle coordinates
    s = np.argsort(c, 0)
    # We're interested in the y coords, which is the second column
    sortList = s[:,1]
    # Confirm we found the 4 circles
    if len(sortList) != 4:
        print "Should have found 4 circles, instead found:", len(sortList)
    # Now fill in the list of circlePoints in the image based
    # on the order in sortList.
    for x in range(len(sortList)):
        circlePointsImage[x] = c[sortList[x]][0:2]
        # While we're at it, draw the circles on the original image
        cv2.circle(img, (icircles[sortList[x]][0], icircles[sortList[x]][1]),
                   icircles[sortList[x]][2], colorList[x%4], 4)

print "Circle points in image:\n", circlePointsImage

# Make a scaled copy to display
scaled = cv2.resize(img, (2592/4, 1944/4))
cv2.namedWindow("Calibration")
cv2.imshow("Calibration", scaled)
cv2.waitKey()

cv2.destroyAllWindows()

if ( len(icircles) == 4 ):
    # At this point, we should have our two arrays, and can create a homography
    h, status = cv2.findHomography(circlePointsImage, circlePointsRobot)
    print "Calculated homography:"
    print h

    print "Save new homography to file (", homographyFile, ")? [Y/n]"
    t = raw_input()
    if (t == 'y') or (t == "Y") or (t == ""):
        np.save(homographyFile, h)
        print "Saved."

else:
    print len(icircles), "circles found. Need 4 for homography matrix."
