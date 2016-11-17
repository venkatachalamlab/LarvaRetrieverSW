Program to drive larva picking robot.

Requires:
	- Python (2.7)
	- Numpy (from \Python27\Scripts directory, run: "pip install numpy")
	- PySerial ("pip install pyserial")
	- OpenCV (https://sourceforge.net/projects/opencvlibrary/files/, extract, then copy cv2.pyd from \OpenCV\build\python\2.7 to \Python27\lib\site-packages)
	- SmoothieBoard drivers (if necessary - http://smoothieware.org/)

Optional:
	- Pronterface (http://www.pronterface.com/)

Usage:

Print "CalibrationPattern.pdf" and ensure that it measures correctly. Cut out square.

CameraCal.py   --- with no gel in place, run this program and follow directions on screen.

ZHeightCal.py  --- with gel in place, and the air line connected and turned on, run this program.

LarvaPicker.py --- run this from a command prompt (cd into the directory containing the script): LarvaPicker.py [n] where n is the size instar you are using (1, 2 or 3).
