import pyaudio # from http://people.csail.mit.edu/hubert/pyaudio/
import serial  # from http://pyserial.sourceforge.net/
import numpy   # from http://numpy.scipy.org/
import audioop
import wave
import sys
import math
import struct
import random

 
MAX = 0



# Mapping
#  10 11 12  1
#   9 16 13  2
#   8 15 14  3
#   7  6  5  4
#  

def bin_to_coordinate(bin):
    if bin == 16:
        return (1,1)
    elif bin == 15:
        return (2,1)
    elif bin == 14:
        return (2,2)
    elif bin == 13:
        return (1,2)
    elif bin == 12:
        return (0,2)
    elif bin == 11:
        return (0,1)
    elif bin == 10:
        return (0,0)
    elif bin == 9:
        return (1,0)
    elif bin == 8:
        return (2,0)
    elif bin == 7:
        return (3,0)
    elif bin == 6:
        return (3,1)
    elif bin == 5:
        return (3,2)
    elif bin == 4:
        return (3,3)
    elif bin == 3:
        return (2,3)
    elif bin == 2:
        return (1,3)
    elif bin == 1:
        return (0,3)

def levels_to_output(levels):
    colors = numpy.zeros(shape=(4,4,3), dtype=numpy.uint8)
    heights = numpy.zeros(shape=(4,4), dtype=numpy.uint8)
    vol_increment = (90.0/4)

    for i in xrange(len(levels)):
        x,y = bin_to_coordinate(i+1)
        heights[x][y] = min(round(levels[i]/vol_increment), 3)
        colors[x][y][0] = round(random.random()*256)
        colors[x][y][1] = round(random.random()*256)
        colors[x][y][2] = round(random.random()*256)

    return colors, heights

def output_to_serial_format((colors, heights)):
    serial_output = numpy.zeros(shape=(4,48), dtype=numpy.uint8)

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
 
def arduino_soundlight(wf):

    chunk      = 2**11 # Change if too fast/slow, never less than 2**11
    scale      = 50    # Change if too dim/bright
    exponent   = 5     # Change if too little/too much difference between loud and quiet sounds
    samplerate = 44100 
    
 
    # CHANGE THIS TO CORRECT INPUT DEVICE
    # Enable stereo mixing in your sound card
    # to make you sound output an input
    # Use list_devices() to list all your input devices
    device   = 0
    
    p = pyaudio.PyAudio()

    print 'lolw ut'

    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    rate = 44100,
                    input = True,
                    frames_per_buffer = chunk,
                    input_device_index = device)
    
    print "Starting, use Ctrl+C to stop"
    try:
        #ser = serial.Serial(
        #    port='com3',
        #    timeout=1
        #)
        print 'lol wut'
        while True:
            data  = stream.read(chunk)
 
            '''
            # Old RMS code, will only show the volume
            
            rms   = audioop.rms(data, 2)
 
            level = min(rms / (2.0 ** 16) * scale, 1.0) 
            level = level**exponent 
            level = int(level * 255)
 
            print level
            ser.write(chr(level))
            '''
 
            # Do FFT
            levels = calculate_levels(data, chunk, samplerate)
            print levels
 
            # Make it look better and send to serial
            # for level in levels:
            #     level = max(min(level / scale, 1.0), 0.0)
            #     level = level**exponent 
            #     level = int(level * 255)
            #     ser.write(chr(level))
 
            # s = ser.read(6)
 
    except KeyboardInterrupt:
        pass
    finally:
        print "\nStopping"
        stream.close()
        p.terminate()
        ser.close()

def arduino_wavefile(wf):

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    CHUNK = 1024
    data = wf.readframes(CHUNK)

    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)
        levels = calculate_levels(data, CHUNK, wf.getframerate())
        print output_to_serial_format(levels_to_output(levels))

    stream.stop_stream()
    stream.close()

    p.terminate()
 
def calculate_levels(data, chunk, samplerate):
    # Use FFT to calculate volume for each frequency
    global MAX
 
    # Convert raw sound data to Numpy array
    fmt = "%dH"%(len(data)/2)
    data2 = struct.unpack(fmt, data)
    data2 = numpy.array(data2, dtype='h')
 
    # Apply FFT
    fourier = numpy.fft.fft(data2)
    ffty = numpy.abs(fourier[0:len(fourier)/2])/1000
    ffty1=ffty[:len(ffty)/2]
    ffty2=ffty[len(ffty)/2::]+2
    ffty2=ffty2[::-1]
    ffty=ffty1+ffty2
    ffty=numpy.log(ffty)-2
    
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
    #list_devices()
    #arduino_soundlight()

