"""Basic WizFi360 HTTP Server / Dispatcher - Alistair MacDonald 2022"""

import wizfi360

# List of page render callback functions
callbacks = []

# Register path hook
def registerpage(path, function):
    callbacks.append([path, function])

# Deregitser path hook
def deregistercallback(path):
    for entry in callbacks:
        if entry[1]==function:
            callbacks.remove(entry)

## Internal functions

# Send a page back through a connection and close it
def sendpage(connection, header="", content="", code="200 OK"):
    #wizfi360.sendbuffer(connection, "HTTP/1.0 " + code + "\r\n" + header.strip("\r\n") + "\r\n\r\n" + content)
    wizfi360.sendbuffer(connection, "HTTP/1.0 " + code + "\r\n" + header.strip("\r\n") + "\r\n\r\n")
    chunkSize = 512
    for chunk in [content[i:i+chunkSize] for i in range(0, len(content), chunkSize)]:
        wizfi360.sendbuffer(connection, chunk)
    wizfi360.close(connection)

# 404 Error dispather for HTTP calls
def sendit_404(connection):
    sendpage(connection, "Content-Type: text/html; charset=utf-8", "<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1></body></html>", "404 Not Found")

# Main dispatcher for HTTP calls
def workit(line):
    lines = line.split("\n")
    # Extract the connection number needed to return data to
    connection = line.split(",", 1)[0]
    # Extract the method (GET/PUT/etc), URL and protocol/version
    request = lines[0][lines[0].find(":")+1:].split(" ")
    method = request[0]
    uriparts = request[1].split("?",1)
    uri = uriparts[0]
    # Parse the params
    params = {}
    if len(uriparts) > 1 :
        for param in uriparts[1].split("&"):
            splitparam = param.split("=",1)
            if len(splitparam) > 1:
                params.update({splitparam[0] : splitparam[1]})
            else:
                params.update({splitparam[0] : None})
    protocol = request[2]
    # Decode the headers
    headers = []
    for header in lines[1:]:
        splitheader = header.split(":", 1)
        if len(splitheader) >= 2:
            headers.append([splitheader[0].strip(" \r"), splitheader[1].strip(" \r")])
    # Call the registers callbacks / hooks
    for entry in callbacks:
        if entry[0]==uri:
            entry[1]({"connection": connection, "method": method, "uri": uri, "params": params, "protocol": protocol, "headers" : headers})
            return True
    # Page not found if a callback was not found
    sendit_404(connection)
    return False


## Hoop in to the wifzfi360 callbacks for page requests
## The server needs stating by the calling code
wizfi360.registercallback(2, workit)
