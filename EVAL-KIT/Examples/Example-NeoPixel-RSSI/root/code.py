# Copyright 2021 Swarm Technologies
#
# Attribution Information:
# https://circuitpython.org/libraries
# https://learn.adafruit.com/adafruit-neopixel-uberguide/python-circuitpython
# https://unexpectedmaker.com/shop/feathers2-esp32-s2
#
# Unless required by applicable law or agreed to in writing, software
# distributed on this device is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import time
import board
import busio
import neopixel

# set up UART for Tile communication
modem = busio.UART(board.TX, board.RX, baudrate=115200, receiver_buffer_size=8192, timeout=0.0)

# initialize variable for Modem Type
global DEVTAG
DEVTAG = None

# initialize variables for RSSI LED
global RSSI_RED, RSSI_GREEN
# These values are default for DN=TILE
RSSI_RED = -91
RSSI_GREEN = -95
pixels = neopixel.NeoPixel(board.IO38, 2, bpp=4, pixel_order=neopixel.GRBW)

# function to read serial data
def readSerial():
    received = modem.read(800)
    if received is not None:
        # convert bytearray to string
        data_string = ''.join([chr(b) for b in received])
        # print serial data string
        print(data_string, end='')
        print('\n')
        # return the serial data string
        return data_string

# function to read RSSI serial message and configure eval kit LED
def setRssiLed(rssiMsg):
    # parse the string for RSSI values - the message is passed as a list
    if 'RSSI' in rssiMsg[1]:
        rssi = rssiMsg[1].split('=')
        rssi = rssi[1].split(',')
        rssi = rssi[0].split('*')
        # convert the RSSI value list to a string
        rssiString = [str(rssi) for rssi in rssi]
        # combine the string
        rssiStringJoin = "".join(rssiString)
        # convert the RSSI value to an integer
        irssi = int(rssiStringJoin)
        # set the LED color based on the RSSI value
        if irssi > RSSI_RED:
            pixels[0] = (16, 0, 0, 0)
        elif irssi < RSSI_GREEN:
            pixels[0] = (0, 16, 0, 0)
        else:
            pixels[0] = (16, 16, 0, 0)
        pixels.write()

#get RSSI value every 5 seconds
modem.write(b'$RT 5*13\n')
readSerial()

while True:
    # read the serial data
    serialData = readSerial()
    time.sleep(1.00)
    # check the data to make sure it is not None
    if serialData is not None:
        # parse the serial data
        parse = serialData[:-3].split(' ')
        # get the Modem Type if it is not already acquired
        if DEVTAG == None:
            # acquire the device information from the Modem
            modem.write(b'$CS*10\n')
            if parse[0] == "$CS":
                if ',' in parse[1]:
                    cs_params = parse[1].split(',')
                for param in cs_params:
                    k, v = param.split('=')
                    if k == "DN":
                        global DEVTAG
                        DEVTAG = v.strip('*')
        # check if it is a RSSI message
        if parse[0] == '$RT':
            # pass the data to the function that will set the color for the on board LED
            setRssiLed(parse)


