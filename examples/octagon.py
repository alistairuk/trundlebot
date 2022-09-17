"""Trundlebot octagon example"""

# Import the trundle library
# You need to do this before you call any trundle commands
import trundle

# Loop through these commands 8 times
for x in range(8):
    # Drive forward 50cm
    trundle008.forward(50)
    # Turn right 45 degrees
    trundle008.right(45)

# Wait for 5 seconds
# This gives us time to press the reset button if we want to stop
sleep(5)

# Turn left a full circle (anticlockwise)
# This is so we can untable the wire
trundle008.left(360)
