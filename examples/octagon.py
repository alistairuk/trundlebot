"""Trundlebot octagon example"""

# Import the trundle library
# You need to do this before you call any trundle commands
import trundle

# Loop through these commands 8 times
for x in range(8):
    # Drive forward 50cm
    trundle.forward(50)
    # Turn right 45 degrees
    trundle.right(45)
