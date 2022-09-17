"""Trundlebot circle example"""

# Import the trundle library
# You need to do this before you call any trundle commands
import trundle

# Loop through these commands 8 times
for x in range(360):
    # Drive forward 50cm
    trundle.forward(1)
    # Turn right 45 degrees
    trundle.right(1)


