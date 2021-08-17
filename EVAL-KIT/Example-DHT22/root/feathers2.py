# FeatherS2 Helper Library
# 2021 Seon Rozenblum, Unexpected Maker
#
# Project home:
#   https://feathers2.io
#

# Import required libraries
import time
import board
from digitalio import DigitalInOut, Direction, Pull
   
# Helper functions

def led_blink():
    """Set the internal LED IO13 to it's inverse state"""
    led13.value = not led13.value

def led_set( state ):
    """Set the internal LED IO13 to this state"""
    led13.value = state

def enable_LDO2(state):
    """Set the power for the second on-board LDO to allow no current draw when not needed."""
    ldo2.value = state
    # A small delay to let the IO change state
    time.sleep(0.035)

def dotstar_color_wheel(wheel_pos):
    """Color wheel to allow for cycling through the rainbow of RGB colors."""
    wheel_pos = wheel_pos % 255

    if wheel_pos < 85:
        return 255 - wheel_pos * 3, 0, wheel_pos * 3
    elif wheel_pos < 170:
        wheel_pos -= 85
        return 0, wheel_pos * 3, 255 - wheel_pos * 3
    else:
        wheel_pos -= 170
        return wheel_pos * 3, 255 - wheel_pos * 3, 0

# Init Blink LED
led13 = DigitalInOut(board.LED)
led13.direction = Direction.OUTPUT

# Init LDO2 Pin
ldo2 = DigitalInOut(board.LDO2)
ldo2.direction = Direction.OUTPUT
