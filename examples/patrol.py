"""Trundlebot patrol example"""

# Import the trundle library
# You need to do this before you call any trundle commands
import trundle

# Move to the start position
trundle.right(90)
trundle.forward(150)
trundle.left(90)

# Move along a line and back again indefinitely
while True:
    trundle.left(90)
    trundle.forward(300)
    trundle.right(180)
    trundle.forward(300)
    trundle.left(90)
