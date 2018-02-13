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

Test connection to robot using Pronterface. The port the board is using can be checked in the Device Manager and the baudrate is 19,200.  Should be able to home robot, then drive in X/Y/Z (positive directions in X/Y to start, negative in Z). If the robot gives "print paused @__" use command M999- ALWAYS RE-HOME ROBOT AFTER THIS COMMAND

Should also be able to open solenoid valves with M42 and M44 commands (type into Pronterface). M43 / M45 close valves. M105 reads the pressure sensor. Pressure is controlled by four valves, the air and vacuum valves directly on the lab wall, and the two small valves on robot (one labeled AIR, one un-labeled- vacuum). 

Can add buttons in Pronterface for those actions. This can be done by using the plus button on the bottom of the grid. 

Adjust flow control valves, shooting for a reading of ~48 when vacuum is open, and, ~20 for air.

Edit CameraCal.py and ImageCapture.py to use appropriate camera number in cv2.VideoCapture() call. If this is the only camera connected to the system, camera number should be 0.

ImageCapture.py -- displays live image of camera with margin overlay. Space bar saves image to file. Also useful to align camera. When saving an image, its seems like the program takes a minute or two to do so. Attempting to view the image or close the ImageCapture window too soon will cause the image to fail to save.

- If image isnt being saved when space bar is pressed, type "ImageCapture.py" directly into command terminal by typing "CMD" in the directory of the LarvaPicker file 

ZHeightCal.py  --- with agar gel in place, and the air/vac lines connected and turned on, run this program to calibrate Z height of bed. The readings should gradually increase until around 52.5 and then stop. If this isnt happening, check code. 

CameraCal.py   --- run this program and follow directions on screen to connect machine coordinates to camera image coordinates. Lighting and contrast crucial for this step, trobuleshoot by trying different lighting set-ups. 

LarvaPicker.py --- watches for a change in the image file, grabs larvae that are in margin when image updates. Edit "instar" variable to adjust for size differences in larvae.
