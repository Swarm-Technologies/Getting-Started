# Copyright 2021 Swarm Technologies
#
# Attribution Information:
# https://circuitpython.org/libraries
# https://learn.adafruit.com/adafruit-neopixel-uberguide/python-circuitpython
# https://www.adafruit.com/product/464
# https://learn.adafruit.com/smart-measuring-cup
# https://unexpectedmaker.com/shop/feathers2-esp32-s2
#
# Unless required by applicable law or agreed to in writing, software
# distributed on this device is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import time
import board
import busio
import analogio
import neopixel
from binascii import hexlify

# set up UART for Tile communication
tile = busio.UART(board.TX, board.RX, baudrate=115200, receiver_buffer_size=8192, timeout=0.0)

# set up pixels LED on eval kit
pixels = neopixel.NeoPixel(board.IO38, 2, bpp=4, pixel_order=neopixel.GRBW)

# set the sensor's input pin to measure the analog voltage
sensorPin = analogio.AnalogIn(board.A0)

# sensor voltage with no liquid
lowLevelVoltage = 2.50

# initialize variable for datetime reference
refDateTime = 0

# function to calculate checksum for Tile commands
def makeTileCmd(cmd):
  cbytes = cmd
  cs = 0
  for c in cbytes[1:]:
    cs = cs ^ c
  return cbytes + b'*%02X\n'%cs

# function to read serial data
def readSerial():
    received = tile.read(800)
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
        if irssi > -91:
            pixels[0] = (16, 0, 0, 0)
        elif irssi < -95:
            pixels[0] = (0, 16, 0, 0)
        else:
            pixels[0] = (16, 16, 0, 0)
        pixels.write()

# function to read the datetime value from the Tile and to trigger a sensor read
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
                sensorVoltage(refDateTime)

def sensorVoltage(timestamp):
    # read the voltage level from the sensor
    voltage = (sensorPin.value * 3.3) / 65536
    # higher voltage reading = lower water level
    if voltage >= lowLevelVoltage:
        print('send email')
        # enter email addresses here
         this line is intentionally uncommented to ensure that the command below is updated with valid email addresses. Comment this line once the email addresses have been updated
        tdCommand = b'$TD AI=65000,"{"t": "to email address", "f": "from email address", "s": "Water Level Alert", "m": "Water level in tank is too low", "i": 1}"'
    else:
        dataString = '{}, {}'.format(timestamp, voltage)
        # add $TD command and convert dataString to HEX
        # conversion to HEX is required for the symbols
        tdCommand = b'$TD ' + hexlify(dataString.encode())
        # Write the command to the Tile
    tile.write(makeTileCmd(tdCommand))

# get RSSI value every 5 seconds
tile.write(b'$RT 5*13\n')

# set the rate of date/time messages to 5 seconds
tile.write(b'$DT 5*05\n')

readSerial()

print('******************************')
print('Liquid Level Sensor Example Running')
print('******************************')

while True:
    # read the serial data
    serialData = readSerial()
    time.sleep(1.00)
    # check the data to make sure it is not None
    if serialData is not None:
        # parse the serial data
        parse = serialData[:-3].split(' ')
        # check if it is a RSSI message
        if parse[0] == '$RT':
            # pass the data to the function that will set the color for the on board LED
            setRssiLed(parse)
        elif parse[0] == '$DT':
            # store the dateTime value
            getTime(parse)

    #print((sensorPin.value * 3.3) / 65536)
