import numpy as np


homographyFile = "homography.npy"
zHeightMapFile = "zHeightMap.npy"
imageFile = "TestImg.png"


margin = 150 # px
centerSize = 450 # px

# Larva area ranges, in px, for 3 instar sizes
larvaRanges = np.array([ [25, 160],
                         [75, 300],
                         [100, 700]])

# Dimensions and distances in millimeters
ZTravel = -10.
ZPickups = [0.2, 0.3, 0.6]
ZDropoffs = [0.3, 0.6, 0.7]
ZExtents = -22.5

minVacReading = 45
