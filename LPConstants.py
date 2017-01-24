import numpy as np


homographyFile = "homography.npy"
zHeightMapFile = "zHeightMap.npy"
imageFile = "TestImg.png"


margin = 150 # px
centerSize = 450 # px

# Larva area ranges, in px, for 3 instar sizes
larvaRanges = np.array([ [25, 110],
                         [75, 200],
                         [100, 700]])

# Dimensions and distances in millimeters
ZTravel = -10.
ZPickups = [0.2, 0.2, 0.2]
ZDropoffs = [0.7, 0.0, 1.3]
ZExtents = -22.5

minVacReading = 45
