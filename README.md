Program to drive larva picking robot.

Requires:
	- Basler Pylon GigE camera driver & viewer (http://www.baslerweb.com/en/products/software)
	- Python (2.7 - https://www.python.org/downloads/release/python-2712/)
	- Numpy (within \Python27\Scripts directory, run: "pip install numpy")
	- PySerial ("pip install pyserial")
	- OpenCV (https://sourceforge.net/projects/opencvlibrary/files/, extract, then copy cv2.pyd from \OpenCV\build\python\2.7 to \Python27\lib\site-packages)
	- SmoothieBoard drivers (if necessary - http://smoothieware.org/)
	- Pronterface (http://www.pronterface.com/)
	- Environment variables

Usage:

Test connection to robot using Pronterface. The port the board is using can be checked in the Device Manager and the baudrate is 19,200.  Should be able to home robot, then drive in X/Y/Z (positive directions in X/Y to start, negative in Z). If the 

Should also be able to open solenoid valves with M42 and M44 commands (type into Pronterface). M43 / M45 close valves. M105 reads the pressure sensor.

Can add buttons in Pronterface for those actions.

Adjust flow control valves, shooting for a reading of ~48 when vacuum is open, and, ~20 for air.

Edit CameraCal.py and ImageCapture.py to use appropriate camera number in cv2.VideoCapture() call. If this is the only camera connected to the system, camera number should be 0.

ImageCapture.py -- displays live image of camera with margin overlay. Space bar saves image to file. Also useful to align camera. When saving an image, its seems like the program takes a minute or two to do so. Attempting to view the image or close the ImageCapture window too soon will cause the image to fail to save.

ZHeightCal.py  --- with agar gel in place, and the air/vac lines connected and turned on, run this program to calibrate Z height of bed.

CameraCal.py   --- run this program and follow directions on screen to connect machine coordinates to camera image coordinates.

LarvaPicker.py --- watches for a change in the image file, grabs larvae that are in margin when image updates. Edit "instar" variable to adjust for size differences in larvae.
