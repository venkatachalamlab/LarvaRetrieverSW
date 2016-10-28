# Copyright 2016, FlySorter LLC

import numpy as np
import cv2

# Outline of camera calibration steps:
# 0. Use pylon viewer to set exposure, gain, etc.
# 1. Direct robot to move to 2 points.
# 2. At each point, direct user to attach corner
#    of printed calibration pattern
# 3. Capture image with camera
# 4. Detect location of calibration points within image.
# 5. Create homography transformation from points.
# 6. Output homography matrix to config file.

webcam = cv2.VideoCapture(2)

webcam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 2592)
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 1944)

res, img = webcam.read()
print "Image:", img.shape

cv2.namedWindow("Foo")
cv2.imshow("Foo", img)

cv2.waitKey()

webcam.release()

cv2.destroyAllWindows()

pts_src = np.array([[338, 156],[1134, 372],[366, 850],[173, 273]])
pts_dst = np.array([[318, 256],[534, 372],[316, 670],[73, 473]])
h, status = cv2.findHomography(pts_src.astype(float), pts_dst.astype(float))
