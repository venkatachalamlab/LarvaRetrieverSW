# Copyright 2016, FlySorter LLC

import fsSerial
import time
import numpy as np

from LPConstants import *

# General structure of this program:
#
# 1. Initialize serial port to communicate with SmoothieBoard
# 2. Home robot
# 3. Move to first z calibration point in X/Y
# 4. Lower Z height while checking pressure sensor output to find surface
# 5. Repeat from 3.
# 6. Home robot
# 7. Close port
# 8. Create Z height map file
#

# Configuration parameters

testPoints = np.array([ [40., 10.],
               [200., 10.],
               [200., 200.],
               [40., 180.0]], float)

startZHeight = -15.0
zIncrement = 0.1
zHeightMapFile = "zHeightMap.npy"

transitSpeed = 6000

robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

robot.sendSyncCmd("M42\n")
time.sleep(1)

pString = robot.sendCmdGetReply("M105\n")
p = float(pString.split(' ')[1].split(':')[1])
if p < minVacReading:
    print "Low pressure reading (", p, "). Is the pump on/stopcock open?"
    print "Min reading should be:", minVacReading
    robot.sendSyncCmd("M43\n")
    robot.close()
    exit()

# Set threshold for surface based on reading
surfaceThreshold = 52.5
print "Vac reading:", p, "Setting threshold to:", surfaceThreshold


robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("G90\n")
robot.sendSyncCmd("G01 F{0}\n".format(transitSpeed))

measuredHeights = np.zeros((len(testPoints), 3))

for x in range(len(testPoints)):
    pt = testPoints[x]
    print "Point: X{0} Y{1}".format(pt[0], pt[1])
    currentZ = startZHeight
    seek = True
    robot.sendSyncCmd("G01 F{0} X{1} Y{2}\n".format(transitSpeed, pt[0], pt[1]))
    while seek is True:
        print "-- ZHeight:", currentZ
        robot.sendSyncCmd("G01 F2000 Z{0}\n".format(currentZ))
        robot.sendSyncCmd("G04 P250\n")
        pString = robot.sendCmdGetReply("M105\n")
        p = float(pString.split(' ')[1].split(':')[1])
        print "-- Pressure reading:", p
        if ( p > surfaceThreshold ):
            print "Found surface at [ {0}, {1}, {2} ].".format(pt[0],
                                                               pt[1],
                                                               currentZ)
            measuredHeights[x] = np.array([pt[0], pt[1], currentZ])
            startZHeight = currentZ + 2.0
            seek = False
        else:
            currentZ = currentZ - zIncrement
            if ( currentZ < ZExtents ):
                print "No surface found at X{0} Y{1}".format(pt[0], pt[1])
                measuredHeights[x] = np.array([pt[0], pt[1], currentZ+zIncrement])
                seek = False
    robot.sendSyncCmd("G01 F2000 Z{0}\n".format(startZHeight))

robot.sendSyncCmd("M43\n")
robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("M84\n")

robot.close()

print "Measured heights:\n"
print measuredHeights

print "Save new Z heights to file (", zHeightMapFile, ")? [Y/n]"
t = raw_input()
if (t == 'y') or (t == "Y") or (t == ""):
    np.save(zHeightMapFile, measuredHeights)
    print "Saved."
