"""Main WizFi360 Trundlebot Firmware - Alistair MacDonald 2022"""


# Configuration

# The diamiter of the drive wheels
wifi_ssid = "********"
# The distance between the centre of the drive wheels
wifi_key = "********"


# The main code

import wizfi360
import wizhttpsvr
import trundle
import machine
import time

# Command queue of trundle commands
commandqueue = []

# Lock for processing command queue
commandrunning = False


## Internal functions

# Load the index page from a file and send it back
def sendit_index(data):
    # Read the index file in to memory
    with open('index.htm', 'r') as file:
        html = file.readlines()
    # Send back the HTTP header and indes file
    wizhttpsvr.sendpage(data["connection"], "Content-Type: text/html; charset=utf-8", "".join(html))

# Service the run call and add commands to the queue
def sendit_run(data):
    # Send back the HTTP header and indes file
    wizhttpsvr.sendpage(data["connection"])
    # Add the command to the queue
    commandqueue.append(data["params"])

# Process the command queue
def processqueue(timerobj):
    global commandrunning
    if not commandrunning:
        # Enter critical zone
        commandrunning = True
        # Check if we have commands to process
        if len(commandqueue) > 0:
            command = commandqueue.pop(0)
            if "cmd" in command and "val" in command:
                if command['cmd'] == "f":
                    trundle.forward( int(command['val']) )
                if command['cmd'] == "b":
                    trundle.back( int(command['val']) )
                if command['cmd'] == "l":
                    trundle.left( int(command['val']) )
                if command['cmd'] == "r":
                    trundle.right( int(command['val']) )
                if command['cmd'] == "w":
                    time.sleep( int(command['val']) )
        # Exit critical zone
        commandrunning = False

## Startup

# Init the WizFi360 hardware and library
wizfi360.startup(True, 250)

# Connect to your wifi
print( "Connecting to wifi..." )
wizfi360.currentwifimode(1)
wizfi360.currentapconnect(wifi_ssid, wifi_key)

# Start the HTTP server
print( "Starting server..." )
wizfi360.currentmultiplemode(1)
wizfi360.maxconnections(2)
wizfi360.server(1, 80)

# Register callbacks / hooks
wizhttpsvr.registerpage("/", sendit_index)
wizhttpsvr.registerpage("/run", sendit_run)

# Connected, so tell the user what the IP address we have
print( "Server running" )
addresses = wizfi360.localipaddress()
print( "Connect to http://" + addresses["STAIP"] + "/ with your browser." )

# Start the time to process the queue
machine.Timer(period=1000, callback=processqueue)

