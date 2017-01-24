# Copyright 2016, FlySorter LLC

import numpy as np
import cv2

from LPConstants import *

# Program to capture image to a file (imageFile) for testing purposes.
# Use in conjunction with LarvaPicker.py

print "Opening camera"
webcam = cv2.VideoCapture(2)
print "Camera open, setting params."

# Set the w/h
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 2592)
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 1944)

print "Params set. Press space bar in image window to update image file (", imageFile, ")"
print "Escape in image window to exit."

# Grab an image
res, img = webcam.read()

cv2.namedWindow("Image Capture")

(h, w, i) = img.shape

scaled = cv2.resize(img, (2592/4, 1944/4))
cv2.imshow("Image Capture", scaled)

key = -1
while key != 27:
    key = cv2.waitKey(10)
    res, img = webcam.read()
    imgR = img.copy()
    cv2.rectangle(imgR, ((w-h)/2, 0), ((w+h)/2, h), (0, 255, 0), 4)
    cv2.rectangle(imgR, ((w-h)/2+margin, margin), ((w+h)/2-margin, h-margin), (0, 0, 255), 4)
    scaled = cv2.resize(imgR, (2592/4, 1944/4))
    cv2.imshow("Image Capture", scaled)
    if ( key == 32 ):
        cv2.imwrite(imageFile, img)

cv2.destroyAllWindows()
webcam.release()
