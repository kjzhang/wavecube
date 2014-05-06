import serial
from serial.tools.list_ports import comports

class CubeWriter(object):
    BAUD_RATE = 115200
    TIMEOUT = 0

    def __init__(self):
        self.output = serial.Serial('/dev/ttyACM0', self.BAUD_RATE, timeout=self.TIMEOUT)

    def write(self, output):
        self.output.readline()
        self.output.write(output)
