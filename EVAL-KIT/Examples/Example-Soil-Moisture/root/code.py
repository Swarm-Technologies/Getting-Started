# Copyright 2021 Swarm Technologies
#
# Attribution Information:
# https://circuitpython.org/libraries
# https://learn.adafruit.com/adafruit-neopixel-uberguide/python-circuitpython
# https://www.adafruit.com/product/4026
# https://www.adafruit.com/product/3568
# https://unexpectedmaker.com/shop/feathers2-esp32-s2
#
# Unless required by applicable law or agreed to in writing, software
# distributed on this device is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import time
import board
import busio
import neopixel
from binascii import hexlify

from adafruit_seesaw.seesaw import Seesaw

# set up UART for Tile communication
modem = busio.UART(board.TX, board.RX, baudrate=115200, receiver_buffer_size=8192, timeout=0.0)

# initialize the i2c bus
i2c_bus = board.I2C()

# initialize the soil moisture level sensor
soilSensor = Seesaw(i2c_bus, addr=0x36)

# initialize variable for datetime reference
refDateTime = 0

# initialize variable for Modem Type
global DEVTAG
DEVTAG = None

# initialize variables for RSSI LED
global RSSI_RED, RSSI_GREEN
# These values are default for DN=TILE
RSSI_RED = -91
RSSI_GREEN = -95
pixels = neopixel.NeoPixel(board.IO38, 2, bpp=4, pixel_order=neopixel.GRBW)

# function to calculate checksum for Tile commands
def makeModemCmd(cmd):
  cbytes = cmd
  cs = 0
  for c in cbytes[1:]:
    cs = cs ^ c
  return cbytes + b'*%02X\n'%cs

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
        # split the list where there is an '=' symbol
        rssi = rssiMsg[1].split('=')
        # split the list where there is a ',' symbol
        rssi = rssi[1].split(',')
        # split the list where there is a '*' symbol
        rssi = rssi[0].split('*')
        # split the list where there is a new line
        rssi = rssi[0].split('\n')
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

# function to read DHT sensor and transmit data to Tile
def readSensor(timestamp):
    # read the moisture level from the sensor
    moistureLevel = soilSensor.moisture_read()
    # read temp from the sensor (°C)
    temp_c = soilSensor.get_temp()
    time.sleep(1)

    dataString = 'Timestamp: {}, Temp: {}, Moisture Level: {}'.format(timestamp,temp_c, moistureLevel)

    # add $TD command and convert dataString to HEX
    # conversion to HEX is required for the symbols
    tdCommand = b'$TD ' + hexlify(dataString.encode())

    # Write the command to the Tile
    modem.write(makeModemCmd(tdCommand))

def getTime(dateTime):
    global refDateTime
    if ',' in dateTime[1]:
        # split the list where there is a ',' symbol
        dateTime = dateTime[1].split(',')
        # split the list where there is a new line
        dateTime = dateTime[0].split('\n')
        # convert the datetime value list to a string
        dateTimeString = [str(dateTime) for dateTime in dateTime]
        # combine the string
        dateTimeStringJoin = "".join(dateTimeString)
        # convert the datetime value to an integer
        iDateTime = int(dateTimeStringJoin)
        # set the datetime reference if it is the first measurement since power up/reset
        if refDateTime == 0:
            refDateTime = iDateTime
        else:
            # compare the most recent datetime value to the reference
            # check if it has been ~30 minutes since the last datetime measurement
            if iDateTime - refDateTime >= 1800:
                # update the reference datatime value
                refDateTime = iDateTime
                # take a sensor measurement
                readSensor(refDateTime)

print('******************************')
print('Soil Moisture Sensor Example Running')
print('******************************')

# get RSSI value every 5 seconds
modem.write(b'$RT 5*13\n')

# set the rate of date/time messages to 10 seconds
modem.write(b'$DT 10*31\n')

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
        elif parse[0] == '$RT':
            # pass the data to the function that will set the color for the on board LED
            setRssiLed(parse)
        elif parse[0] == '$DT':
            # store the dateTime value
            getTime(parse)


