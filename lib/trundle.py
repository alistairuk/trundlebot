"""Trundlebot base control library - https://github.com/alistairuk/trundlebot"""

__author__ = "Alistair MacDonald"
__copyright__ = "Copyright 2022, Alistar MacDonald"
__license__ = "LGPL"
__version__ = "1.0"
__maintainer__ = "Alisatir MacDonald"
__email__ = "trundlebot@agm.me.uk"


# Configuration

# The diamiter of the drive wheels
wheel_diamiter = 99
# The distance between the centre of the drive wheels
wheel_separation = 138


# The main code

# Import the required libraries
from math import pi
from machine import Pin
from time import sleep

# Set up and seve the output pins
pins_left = [Pin(11,Pin.OUT), Pin(10,Pin.OUT), Pin(9,Pin.OUT), Pin(8,Pin.OUT)]
pins_right = [Pin(12,Pin.OUT), Pin(13,Pin.OUT), Pin(14,Pin.OUT), Pin(15,Pin.OUT)]

# Calculate working variables
wheel_circumference = wheel_diamiter * pi
step_distance = wheel_circumference/2048
turn_circumference = wheel_separation * pi
turn_angle = 360/turn_circumference*step_distance

# Global state variables
pos_left = 0
pos_right = 0

# Internal functions

# Update the stepper control pins
def energise():
    for pin in range(4):
        pins_left[pin].value(pin==pos_left)
        pins_right[pin].value(pin==pos_right)
    sleep(0.01)

# Move stepepr motors positions by one step
def step(direction_left=True, direction_right=True):
    global pos_left, pos_right
    if direction_left:
        pos_left = (pos_left+1) % 4
    else:
        pos_left = (pos_left+3) % 4
    if direction_right:
        pos_right = (pos_right+1) % 4
    else:
        pos_right = (pos_right+3) % 4
    energise()


# Public functions

# Move forward distance (in millimeters)
def forward(distance):
    while distance >= step_distance:
        step(True, True)
        distance -= step_distance
    while distance <= -step_distance:
        step(False, False)
        distance += step_distance

# Move backward distance (in millimeters)
def back(distance):
    forward(-distance)

# Turn right angle (in degrees)
def right(angle):
    while angle >= turn_angle:
        step(True, False)
        angle -= turn_angle
    while angle <= -1:
        step(False, True)
        angle += turn_angle

# Turn left angle (in degrees)
def left(angle):
    right(-angle)
