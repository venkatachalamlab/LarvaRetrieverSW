## Copyright (c) 2016, FlySorter LLC
##

import sys
import glob
import serial
import time

# Serial communications class that is used for multiple devices.
#
class fsSerial:
    """Serial class for generic serial device."""

    WaitTimeout = 3
    portName = ""

    def __init__(self, port, baud = 9600, timeout = float(0.1)):
        self.isOpened = False
        try:
            self.ser = serial.Serial(port, baudrate = baud, timeout = timeout)
        except:
            print "Failed to open port", port
            return
        self.isOpened = True

    def close(self):
        self.ser.close()

    # Retrieve any waiting data on the port
    def getSerOutput(self):
        #print "GSO:"
        output = ''
        while True:
            # read() blocks for the timeout set above *if* there is nothing to read
            #   otherwise it returns immediately
            byte = self.ser.read(1)
            if byte is None or byte == '':
                break
            output += byte
            if byte == '\n':
                break
        #print "GSO Output:", output
        return output

    # Block and wait for the device to reply with "ok" or "OK"
    # Times out after self.WaitTimeout (set above)
    def waitForOK(self):
        #print "WFO:"
        output = ''
        timeoutMax = self.WaitTimeout / self.ser.timeout
        timeoutCount = 0
        while True:
            byte = self.ser.read(1)
            if byte is None or byte == '':
                timeoutCount += 1
                time.sleep(1)
            else:
                output += byte
            if timeoutCount > timeoutMax:
                print 'Serial timeout.'
                break
            if byte == '\n':
                break
        #print "WFO Output:", output
        if (output.rstrip('\r\n') != '') and ( not output.startswith("ok") ) and ( not output.startswith("OK") ):
            print "Unexpected serial output:", output.rstrip('\r\n'), "(", ':'.join(x.encode('hex') for x in output), ")"

    # Send a command to the device via serial port
    # Asynchronous by default - doesn't wait for reply
    def sendCmd(self, cmd):
        #print "SC:", cmd
        self.ser.write(cmd)
        self.ser.flush()

    # Send a command to the device via serial port
    # Waits to receive reply of "ok" or "OK" via waitForOK()
    def sendSyncCmd(self, cmd):
        #print "SSC:", cmd
        self.ser.flushInput()
        self.ser.write(cmd)
        self.ser.flush()
        self.waitForOK()

    # Send a command and retrieve the reply
    def sendCmdGetReply(self, cmd):
        self.ser.flushInput()
        self.ser.write(cmd)
        self.ser.flush()
        return self.getSerOutput()

def listAvailablePorts():
    """Lists serial ports"""

    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(64)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def findDispenser():
    portList = listAvailablePorts()
    for port in portList:
        s = fsSerial(port)
        s.sendCmd('V')
        time.sleep(0.25)
        r=s.getSerOutput()
        if r.startswith("  V"):
            #print "Port:", port, "is first dispenser found"
            dispenser = s
            dispenser.ser.flushInput()
            return dispenser
        s.ser.flushInput()
        s.ser.flushOutput()
        s.close()
    return None

def findSmoothie():
    portList = listAvailablePorts()
    for port in portList:
        s = fsSerial(port)
        r = s.sendCmdGetReply('version\n')
        #print "Reply: ", r
        if r.startswith("Build version:"):
            #print "Port:", port, "is first Smoothie found"
            smoothie = s
            smoothie.ser.flushInput()
            return smoothie
        s.ser.flushInput()
        s.ser.flushOutput()
        s.close()
    return None
