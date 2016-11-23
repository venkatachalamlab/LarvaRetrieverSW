# Copyright 2016, FlySorter LLC

import os
import glob
import sys
import time
import cv2

imageFile = "TestImg.png"

prevTime = os.path.getmtime(imageFile)
img = cv2.imread(imageFile,0)
scaled = cv2.resize(img, (img.shape[1]/4, img.shape[0]/4))
cv2.imshow("Img", scaled)
cv2.waitKey(1)

print "Waiting"

while True:
    try:
        # Check file time
        if ( os.path.getmtime(imageFile) != prevTime ):
            print "Updated!", time.time()
            img = cv2.imread(imageFile,0)
            if img is not None:
                scaled = cv2.resize(img, (img.shape[1]/4, img.shape[0]/4))
                cv2.imshow("Img", scaled)
                cv2.waitKey(1)
                prevTime = os.path.getmtime(imageFile)
        time.sleep(0.1)
    except KeyboardInterrupt:
        break

cv2.waitKey()
cv2.destroyAllWindows()
