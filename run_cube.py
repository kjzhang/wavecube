import pyaudio
import serial
import numpy as np
import audioop
import wave
import sys
import time
import math
import struct
import random

import cube

# Mapping
#  10 11 12  1
#   9 16 13  2
#   8 15 14  3
#   7  6  5  4

time_s = time.time()

bins = {
    0: (0, 3),
    1: (1, 3),
    2: (2, 3),
    3: (3, 3),
    4: (3, 2),
    5: (3, 1),
    6: (3, 0),
    7: (2, 0),
    8: (1, 0),
    9: (0, 0),
    10: (0, 1),
    11: (0, 2),
    12: (1, 2),
    13: (2, 2),
    14: (2, 1),
    15: (1, 1)
}

def bin_to_coordinate(bin):
    return bins[bin]

def levels_to_output(levels):
    print levels
    colors = np.zeros(shape=(4,4,3), dtype=np.uint8)
    heights = np.zeros(shape=(4,4), dtype=np.uint8)
    vol_increment = 180.0 / 4

    time_delta = time.time() - time_s
    beats = 128 * time_delta / 60

    for i in xrange(len(levels)):
        x, y = bin_to_coordinate(i)
        heights[x][y] = np.uint8(min(math.floor(levels[i]/vol_increment), 3))
        colors[x][y][0] = (beats % 3 + 0) / 3 * 255 #np.uint8(round(random.random()*255))
        colors[x][y][1] = (beats % 3 + 1) / 3 * 255 #np.uint8(round(random.random()*255))
        colors[x][y][2] = (beats % 3 + 2) / 3 * 255 #np.uint8(round(random.random()*255))

    return colors, heights

def output_to_serial_format((colors, heights)):
    serial_output = np.zeros(shape=(4,48), dtype=np.uint8)

    for x in xrange(4):
        for y in xrange(4):
            for h in xrange(4):
                if h <= heights[x][y]:
                    serial_output[h][4*x+y] = colors[x][y][0]
                    serial_output[h][4*x+y+16] = colors[x][y][1]
                    serial_output[h][4*x+y+32] = colors[x][y][2]
                else:
                    serial_output[h][4*x+y] = 0
                    serial_output[h][4*x+y+16] = 0
                    serial_output[h][4*x+y+32] = 0
    return serial_output

def list_devices():
    # List all audio input devices
    p = pyaudio.PyAudio()
    i = 0
    n = p.get_device_count()
    while i < n:
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print str(i)+'. '+dev['name']
        i += 1

def arduino_wavefile(wf):

    c = cube.CubeWriter()

    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    CHUNK = 2048

    data = wf.readframes(CHUNK)

    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)
        levels = calculate_levels(data, CHUNK, wf.getframerate())
        output = output_to_serial_format(levels_to_output(levels))

        # print output
        # c.write(output[0].tostring())
        # c.write(output[1].tostring())
        # c.write(output[2].tostring())
        # c.write(output[3].tostring())
        c.write(output.tostring())

    stream.stop_stream()
    stream.close()

    p.terminate()
 
def calculate_levels(data, chunk, samplerate):
    # Use FFT to calculate volume for each frequency
    # Convert raw sound data to Numpy array
    fmt = "%dH" % (len(data) / 2)
    data2 = np.array(struct.unpack(fmt, data), dtype='h')
 
    # Apply FFT
    fourier = np.fft.fft(data2)
    ffty = np.abs(fourier[0:len(fourier)/2])/1000
    ffty1 = ffty[:len(ffty)/2]
    ffty2 = ffty[len(ffty)/2::]+2
    ffty2 = ffty2[::-1]
    ffty = ffty1+ffty2
    ffty = np.log(ffty)-2
    
    fourier = list(ffty)[4:-4]
    fourier = fourier[:len(fourier)/2]
    
    size = len(fourier)
 
    # Add up for 6 lights
    levels = [sum(fourier[i:(i+size/16)]) for i in xrange(0, size, size/16)][:16]

    return levels
 
if __name__ == '__main__':
    if len(sys.argv) < 2:
       print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
       sys.exit(-1)

    wf = wave.open(sys.argv[1], 'rb')
    arduino_wavefile(wf)
