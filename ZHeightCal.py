# Copyright 2016, FlySorter LLC

import fsSerial
import time
import numpy as np

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

testPoints = np.array([ [50.0, 50.0],
               [150.0, 50.0],
               [50.0, 150.0],
               [150.0, 150.0]])

startZHeight = -10.0
zIncrement = 0.25
zExtents = -12.0
transitSpeed = 1000

zHeightMapFile = "zHeightMap.npy"

robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

robot.sendSyncCmd("M44\n")
time.sleep(1)

pString = robot.sendCmdGetReply("M105\n")
p = float(pString.split(' ')[1].split(':')[1])
if p < 35.0:
    print "Low pressure reading. Is the air on?"
    robot.sendSyncCmd("M45\n")
    robot.close()
    exit()

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("G90\n")

measuredHeights = np.zeros((len(testPoints), 3))

for x in range(len(testPoints)):
    pt = testPoints[x]
    print "Point: X{0} Y{1}".format(pt[0], pt[1])
    currentZ = startZHeight
    seek = True
    robot.sendSyncCmd("G01 F{0} X{1} Y{2}\n".format(2*transitSpeed, pt[0], pt[1]))
    while seek is True:
        print "-- ZHeight:", currentZ
        robot.sendSyncCmd("G01 F{0} Z{1}\n".format(transitSpeed, currentZ))
        robot.sendSyncCmd("G04 P250\n")
        pString = robot.sendCmdGetReply("M105\n")
        p = float(pString.split(' ')[1].split(':')[1])
        print "-- Pressure reading:", p
        if ( p > 43.5 ):
            print "Found surface at [ {0}, {1}, {2} ].".format(pt[0],
                                                               pt[1],
                                                               currentZ)
            measuredHeights[x] = np.array([pt[0], pt[1], currentZ])
            seek = False
        else:
            currentZ = currentZ - zIncrement
            if ( currentZ < zExtents ):
                print "No surface found at X{0} Y{1}".format(pt[0], pt[1])
                seek = False
    robot.sendSyncCmd("G01 F{0} Z{1}\n".format(transitSpeed, startZHeight))  

print measuredHeights

np.save(zHeightMapFile, measuredHeights)
                           
robot.sendSyncCmd("M45\n")
robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("M84\n")

robot.close()
