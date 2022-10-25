"""WizFi360 Abstraction Library - Alistair MacDonald 2022"""

## From specification at https://docs.wiznet.io/img/products/wizfi360/wizfi360ds/wizfi360_atset_v1118_e.pdf

import machine
import time

uart_port = 1
uart_default_baud = 115200
uart_timeout = 28
reset_pin = 20
default_response_timeout = 80000

# Deactivate the reset pin
resetpin = machine.Pin(reset_pin, machine.Pin.OUT)
resetpin.value(1)

# Open the UART
uart = machine.UART(uart_port, uart_default_baud, timeout=uart_timeout)
dirtybuffer = False # Flag if the buffer could have residual end of reresponsesponces line in it?
multiconnect = False # Are we expecting the Link ID?

# List of callback functions
networkcallbacks = []

# Globals for remembering callback data
holdoffirq=False

## Internal functions

# Register for a network data callback (callbacktype = 1 for connect, 2 for data, and 3 for close)
def registercallback(callbacktype, function):
    networkcallbacks.append([callbacktype, function])

# Deregitser for a network data callback
def deregistercallback(callbacktype, function):
    for entry in networkcallbacks:
        if entry[0]==callbacktype and entry[1]==function:
            networkcallbacks.remove(entry)

# Identify if this was a positive response
def ispositive(response):
    return (response=="OK") or response.startswith("SEND OK")

# Identify if this was a negative response
def isnegative(response):
    return (response=="ERROR") or (response=="ALREADY CONNECTED") or (response=="SEND FAIL") or (response=="NOT GPIO MODE!")

# Identify if this is the completion of a response
def isdefinitive(response, custom=None):
    if custom is not None:
        return ispositive(response) or isnegative(response) or response.startswith(custom)
    else:
        return ispositive(response) or isnegative(response)

# Extract the [first/only] parameter from a response 
def extractval(parameter, response, default=None):
    for entry in response:
        if entry.startswith(parameter):
            return (entry[len(parameter):]).strip()
    return default

# Extract all parameter from a response 
def extractvals(parameter, response):
    result = []
    for entry in response:
        if entry.startswith(parameter):
            result.append((entry[len(parameter):]).strip())
    return result

# Extract all parameter from a response and split them
def extractvalssplit(parameter, response):
    result = []
    for entry in response:
        if entry.startswith(parameter):
            result.append((entry[len(parameter):]).strip().split(','))
    return result

# Read a lines of response from the UART
def readline():
    stringin = ""
    while (True):
        charin = uart.read(1)
        # If we time out we are at the end of a line
        if charin is None:
            return stringin
        # We this the end of the line?
        elif (charin == b'\r'):
            if (stringin!=""):
                return stringin
        # This will be part of the string then
        elif not (charin == b'\n'):
            stringin += chr(ord(charin))
            
# Check if we have a callback hook for this line
def processcallbacks(line):
    # Check for network connection
    if line.endswith(",CONNECT"):
        for entry in networkcallbacks:
            if entry[0]==1:
                entry[1](line[:-8])
    # Check for network close
    if line.endswith(",CLOSED"):
        for entry in networkcallbacks:
            if entry[0]==3:
                entry[1](line[:-7])
    # Check for network data
    if line.startswith("+IPD,"):
        for entry in networkcallbacks:
            if entry[0]==2:
                entry[1](line[5:])
                
# If that start of a data buffer for  unsolicited result codes 
def readremainingipd(line):
    splitline = line.split(":",1)
    # Work out how much data is remaing in the buffer
    if multiconnect:
        length = splitline[0].split(",")[2]
    else:
        length = splitline[0].split(",")[1]
    remaining = int(length) - len(splitline[0])
    # Read the remainng data
    result = uart.read(remaining)
    return result.decode("utf-8")

# Process the buffer for  unsolicited result codes 
def processbuffer():
    while uart.any()>0:
        line = readline()
        # If there is binary data then read the rest in
        if line.startswith("+IPD,"):
            line += readremainingipd(line)
        # Process the line of data
        processcallbacks(line)
        
# Execute a command on the module
def command(command="AT", response_timeout=default_response_timeout, required_response=None, custom_endofdata=None):
    global dirtybuffer
    global holdoffirq
    # Don't let the interupt process the buffer mid command
    holdoffirq = True
    # Process anything remaining in the buffer
    processbuffer()
    # Send the command
    uart.write(command + "\r\n")
    # Read the results
    result = []
    complete = False
    customcomplete = required_response is None
    timeouttime = time.time()+(response_timeout/1000)
    while (time.time()<timeouttime):
        line = readline()
        processcallbacks(line)
        # Remember the line if not empty
        if (len(line)>0):
            result.append(line)
        # Check if we have a standard end of response
        if isdefinitive(line, custom_endofdata):
            complete = True
        # Check if we have the data we are looking for
        if (required_response is not None) and (line.startswith(required_response)):
            customcomplete = True
        # Check if we are done
        if complete and customcomplete:
            holdoffirq = False
            return result
    # We ran out of time
    # set the dirty buffer flag is an out of date end of responcs cound end up in the buffer
    if required_response is None:
        dirtybuffer = True
    result.append("TIMEOUT")
    holdoffirq = False
    return result

# Netlight sheduled (called for polling uart)
def uartcheckscheduled_internal(timerobj):
    # Check for incomming commands
    if holdoffirq==False:
        processbuffer()

# [Optionally] send a command to change a setting, and retreve the current/new setting
# For most commands with a command name for get and set commands, and the result prefix
def commandsetandget(command_name, settingstring=None, multiple=False):
    # Set the new setting if we have one to set
    if settingstring is not None:
        command("AT+" + command_name + "=" + str(settingstring))
    # Retieve the current/new setting
    response = command("AT+" + command_name + "?")
    if multiple is not None:
        current = extractvals("+" + command_name + ":", response)
    else:
        current = extractval("+" + command_name + ":", response)
    # Return the current setting
    return current

## System control commands

# Send AT command to test the WizFi360 module
def test():
    return command("AT")

# Hardware reset the WizFi360 module
def reset():
    resetpin.value(0)
    resetpin.value(1)
    time.sleep(0.5)

# Soft restart the WizFi360 module
def restart():
    return command("AT+RST")

# Check version information
### Do some more processing on results
def version():
    return command("AT+GMR")

# Enter deep-sleep mode (sleeptime in ms)
def deepsleep(sleeptime):
    return command("AT+GSLP=" + str(sleeptime))

# Disable command echoing
def disableecho():
    return command("ATE0")

# Enable command echoing
def enableecho():
    return command("ATE1")

# Restores factory default settings (restoretype = 0 for mac address, or 1 for all setting)
def factorydefaults(restoretype):
    return command("AT+RESTORE=" + str(restoretype))

# Get/set the current UART configuration (not saved to flash, settingstring and/or result = <baudrate>,<databits>,<stopbits>,<parity>,<flow control>)
def currentuartconf(settingstring=None):
    return commandsetandget("UART_CUR", settingstring).split(",")

# Get/set the default UART configuration (saved in flash, settingstring and result/or = <baudrate>,<databits>,<stopbits>,<parity>,<flow control>)
def defaultuartconf(settingstring=None):
    return commandsetandget("UART_DEF", settingstring).split(",")

# Configure sleep mode (sleepmode = 0 disabled, 1 for light sleep mode, or 2 for : modem sleep mode (default))
def sleepmode(sleepmode=None):
    return commandsetandget("SLEEP", sleepmode)

# Set the I/O pin mode (pin=pin number, mode=0 is default mode and 1 is GPIO mode, pullup=0 for floating or 1 for pullup)
def ioworkingmode(pin, mode=None, pullup=0):
    return command("AT+SYSIOSETCFG=", str(pin) + "," + str(mode) + "," + str(pullup))

# Set the GPIO pin direction (pin=pin number, direction=0 is for input and 1 is for output)
def gpiodirection(pin, direction):
    return command("AT+SYSGPIODIR=" + str(pin) + "," + str(direction))

# Set the GPIO pin level (pin=pin number, level=0 for low and 1 for high)
def gpiowrite(pin, level):
    return command("AT+SYSGPIOWRITE=" + str(pin) + "," + str(level))

# Get the GPIO pin level (pin=pin number, returns <pin><dir><level>)
def gpioread(pin):
    return commandsetandget("SYSGPIOREAD")


## WiFi commands


# Get/set the current WiFi mode (not saved to flash, mode / result = 1 for Station mode, 2 for SoftAP mode, 3 for Station + SoftAP mode)
def currentwifimode(mode=None):
    return commandsetandget("CWMODE_CUR", mode)

# Get/set the WiFi mode (saved in flash, mode / result = 1 for Station mode, 2 for SoftAP mode, 3 for Station + SoftAP mode)
def defaultwifimode(mode=None):
    return commandsetandget("CWMODE_DEF", mode)

# Connects to an AP (not saved to flash, mode / result = 1 for Station mode, 2 for SoftAP mode, 3 for Station + SoftAP mode)
def currentapconnect(ssid, password, bssid=None):
    settingstring = "\"" + str(ssid) + "\",\"" + str(password) + "\"";
    if bssid is not None:
        settingstring += ",\"" + str(bssid) + "\""
    return commandsetandget("CWJAP_CUR", settingstring)

# Connects to an AP (saved in flash, mode / result = 1 for Station mode, 2 for SoftAP mode, 3 for Station + SoftAP mode)
def defaultapconnect(ssid, password, bssid=None):
    settingstring = str(ssid) + "," + str(password);
    if bssid is not None:
        settingstring += "," + str(bssid)
    return commandsetandget("CWJAP_DEF", settingstring)


#    sAT+CWLAPOPT Sets the Configuration for the Command AT+CWLAP


# Lists Available APs
def listaps(ssid=None, mac=None, channel=None):
    # Build the request
    commandstring = "AT+CWLAP";
    if ssid is not None:
        commandstring += "=\"" + str(ssid) + "\""
    if mac is not None:
        commandstring += ",\"" + str(mac) + "\""
    if channel is not None:
        commandstring += "," + str(channel)
    # Execute the command and extract the result
    response = command(commandstring)
    return extractvalssplit("+CWLAP:", response)


#    AT+CWQAP Disconnects from the AP
#    AT+CWSAP_CUR Configures the WizFi360 SoftAP; Configuration Not Saved in the Flash
#    AT+CWSAP_DEF Configures the WizFi360 SoftAP; Configuration Saved in the Flash
#    AT+CWLIF IP of Stations to Which the WizFi360 SoftAP is Connected
#    AT+CWDHCP_CUR Enables/Disables DHCP; Configuration Not Saved in the Flash
#    AT+CWDHCP_DEF Enables/Disables DHCP; Configuration Saved in the Flash
#    AT+CWDHCPS_CUR Sets the IP Address Allocated by WizFi360 SoftAP DHCP; Configuration Not Saved in Flash WizFi360 AT Command 9 / 66
#    AT+CWDHCPS_DEF Sets the IP Address Allocated by WizFi360 SoftAP DHCP; Configuration Saved in Flash
#    AT+CWAUTOCONN Auto-Connects to the AP or Not
#    AT+CIPSTAMAC_CUR Sets the MAC Address of the WizFi360 Station; Configuration Not Saved in the Flash
#    AT+CIPSTAMAC_DEF Sets the MAC Address of the WizFi360 Station; Configuration Saved in the Flash
#    AT+CIPAPMAC_CUR Sets the MAC Address of the WizFi360 SoftAP; Configuration Not Saved in the Flash
#    AT+CIPAPMAC_DEF Sets the MAC Address of the WizFi360 SoftAP; Configuration Saved in the Flash


# Get/set the current station mode IP address (ip, gateway, and netmask are all )
### Do some more processing on results
def currentipaddress(ip=None, gateway=None, netmask=None):
    # Build the request
    settingstring = "=\"" + str(ip) + "\""
    if gateway is not None:
        settingstring += ",\"" + str(gateway) + "\""
    if netmask is not None:
        settingstring += ",\"" + str(netmask) + "\""
    # Execute the command and extract the result
    response = commandsetandget("CIPSTA_CUR", settingstring, True)
    resultlist = {}
    for entry in response:
        splitentry = entry.replace("\"", "").split(":")
        resultlist.update({splitentry[0]:splitentry[1]})
    return resultlist

# Get/set the default station mode IP address (ip, gateway, and netmask are all )
### Do some more processing on results
def defaultipaddress(ip=None, gateway=None, netmask=None):
    # Build the request
    settingstring = "=\"" + str(ip) + "\""
    if gateway is not None:
        settingstring += ",\"" + str(gateway) + "\""
    if netmask is not None:
        settingstring += ",\"" + str(netmask) + "\""
    # Execute the command and extract the result
    response = commandsetandget("CIPSTA_DEF", settingstring, True)
    resultlist = {}
    for entry in response:
        splitentry = entry.replace("\"", "").split(":")
        resultlist.update({splitentry[0]:splitentry[1]})
    return resultlist


#    AT+CIPAP_CUR Sets the IP Address of the WizFi360 SoftAP; Configuration Not Saved in the Flash
#    AT+CIPAP_DEF Sets the IP Address of the WizFi360 SoftAP; Configuration Saved in the Flash
#    AT+CWSTARTSMART Start SmartConfig
#    AT+CWSTOPSMART Stop Smart Config
#    AT+WPS Enables the WPS Function
#    AT+CWHOSTNAME Configures the Name of WizFi360 Station
#    AT+CWCOUNTRY_CUR Set WiFi Country Code of WizFi360; Configuration Not Saved in the Flash
#    AT+CWCOUNTRY_DEF Set WiFi Country Code of WizFi360; Configuration Saved in the Flash
#    AT+WIZ_NETCONFIG WebServer for setting SSID/PWD (Default: 192.168.36.1)


## TCP / IP commands


#    AT+CIPSTATUS Gets the Connection Status
#    AT+CIPDOMAIN DNS Function
#    AT+CIPSTART Establishes TCP Connection, UDP Transmission or SSL Connection
#    AT+CIPSSLSIZE Sets the Size of SSL Buffer
#    AT+SSLCCONF Sets Configuration of WiFi360 SSL Client
#    AT+CASEND Sets the SSL certificate
#    AT+CIPSEND Send data
#    AT+CIPSENDEX Sends data when length of data is <length>, or when \0 appears in the data


# Writes data into the TCP send buffer
def sendbuffer(linkid=None, data=""):
    # Build the request
    commandstring = "AT+CIPSENDBUF=";
    if linkid is not None:
        commandstring += str(linkid) + ","
    commandstring += str(len(data))
    # Send the request
    result = command(commandstring)
    if ispositive(result[-1]):
        uart.write(data)
    return result


#    AT+CIPBUFRESET Resets the Segment ID Count
#    AT+CIPBUFSTATUS Checks the Status of TCP-Send-Buffer
#    AT+CIPCHECKSEQ Checks If a Specific Segment Was Successfully Sent

# Close a TCP/UDP/SSL Connection
def close(linkid=None):
    if linkid is not None:
        return command("AT+CIPCLOSE=" + str(linkid))
    else:
        return command("AT+CIPCLOSE")

# Get the local IP and MAC address
def localipaddress():
    response = command("AT+CIFSR")
    resultlist = {}
    for entry in extractvals("+CIFSR:", response):
        splitentry = entry.split(",")
        resultlist.update( { splitentry[0] : splitentry[1].replace("\"", "") } )
    return resultlist

# Get/set the multiple connections mode (mode / result = 0 for single connection, or 1 for multiple connections)
def currentmultiplemode(mode=None):
    global multiconnect
    if mode==0:
        multiconnect = False
    if mode==1:
        multiconnect = True
    return commandsetandget("CIPMUX", mode)

# Creates/deletes a TCP server (mode = 0 for delete or 1 for create, port = TCP/IP port number)
def server(mode=1, port=None):
    commandstring = "AT+CIPSERVER=" + str(mode)
    if port is not None:
        commandstring += "," + str(port)
    return ispositive(command(commandstring)[-1])

# Get/set the maximum incoming server connections allowed (number / result = 1 to 4 connections)
def maxconnections(number=None):
    return commandsetandget("CIPSERVERMAXCONN", number)

#    AT+CIPMODE Sets transmission mode
#    AT+SAVETRANSLINK Saves the Transparent Transmission Link in Flash;
#    AT+CIPSTO Sets the TCP Server Timeout
#    AT+CIUPDATE Update the Firmware

# Send an ICMP Ping packet (address=host name or IP address, returns true is sucsessful)
def ping(address):
    return ispositive(command("AT+PING=\"" + str(address) + "\"")[-1])


#    AT+CIPDINFO Shows the Remote IP and Port with +IPD
#    AT+CIPSNTPCFG Sets the Configuration of SNTP
#    AT+CIPSNTPIME Checks the SNTP Time
#    AT+CIPDNS_CUR Sets User-defined DNS Servers; Configuration Not Saved in the Flash
#    AT+CIPDNS_DEF Sets User-defined DNS Servers; Configuration Saved in the Flash
#    AT+MQTTSET Sets the Configuration of MQTT connection
#    AT+MQTTTOPIC Sets the Topic of Publish and Subscribe
#    AT+MQTTQOS Sets the Configuration of QoS
#    AT+MQTTCON Connects to a Broker
#    AT+MQTTPUB Publish a message
#    AT+MQTTPUBSEND Publish a message
#    AT+MQTTDIS Disconnects from a Broker
#    AT+AZSET Sets the Configuration of Azure IoT Hub connection
#    AT+AZCON Connects to a Azure IoT Hub
#    AT+AWSPKSEND Sets Private Key
#    AT+CLICASEND Sets Client Certificate
#    AT+AWSCON Connects to AWS IoT Core


## Startup...

# This is to be called to init this library (hardwarereset = Ture to toggle reset pin, pollperiod is the frequency to check for new data in ms)
def startup(hardwarereset=True, pollperiod=1000):
    # Haerdware reset the WizFi360 if hardware if requirted
    if hardwarereset:
        reset()
    # Start periodic time for polling UART
    machine.Timer(period=pollperiod, callback=uartcheckscheduled_internal)
