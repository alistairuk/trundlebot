"""Trundlebot decision example"""

# Import the trundle library
# You need to do this before you call any trundle commands
import trundle

# Import the random library so we can make random numbers
import random

# Move a little before making a decision
for x in range(random.randint(3, 6)):
    # Move randomly to the right or left randomly
    if random.randint(0,1) == 1:
        trundle.right(25)
        trundle.left(25)
    else:
        trundle.left(25)
        trundle.right(25)

# Make the decision and do the action
if random.randint(0,1) == 1:
    # Yes
    trundle.right(45)
    trundle.forward(60)
    trundle.left(45)
    for y in range(3):
        trundle.forward(10)
        trundle.back(20)
        trundle.forward(10)
else:
    # No
    trundle.left(45)
    trundle.forward(60)
    trundle.right(45)
    for y in range(3):
        trundle.right(15)
        trundle.left(30)
        trundle.right(15)

