# Should include
#   - Algorithm
#   - Communication between all nodes
#   - Polling price from NordPool

# May have this structures:
#   - WaitingList = {id, time, power, (group id), deadline}
#   - Price = {Hour, avg price}


import socketserver
import json
import download_price
import socket
import threading

node_list = {} # Tuple with all known devices
waiting_list = {} # Tuple with all waiting background loads
active_list = {} # Tuple with all active devices
background_list = {} # Tuple with all known background devices(active and inactive)
current_power = 0 
threshold = 1500  # maximum allowed power
pricelist = {} # keeps track of the following days hourly electricaly price

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        while True:
            # Try to receive
            data = self.request.recv(1024)
            if not data:
                return
            data = data.decode('utf-8')
            try:
                data = json.loads(data)
            except Exception as e:
                print (e)
                continue

            print (data)
            action = data['action']
            payload = data['payload']

            # Register action
            if (action == 'register'):
                self.handle_register(payload)

            # Request action
            elif (action == 'request'):
                self.handle_request(payload)

            # Update action
            elif (action == 'update'):
                self.handle_update(payload)

            # Disconnect action
            elif (action == 'disconnect'):
                self.handle_disconnect(payload)

            # Invalid, drop it 
            else:
                print('Invalid action received')

            # Reset
            action = ''
            payload = ''
            data.clear()

    def handle_register(self, payload):
        # Add the node to the list of all nodes
        print('Register from node: ' + str(payload['id']))
        node_list[payload['id']] = payload['details']

        # Check if the node is a background task
        if (payload['details']['flexible'] == 1):
            background_list[payload['id']] = payload['details']

    def handle_request(self, payload):
        global current_power, threshold

        print('Request from node: ' + str(payload['id']))
        
        # Get the tuple of details based on the requested node's id
        details = node_list[payload['id']]
        
        # Check which flexibility the node has
        # Interactive load
        if (details['flexible'] == 0):
            print('Interactive load')
            # Add the power to the total consumption
            current_power += details['power']
            
            # Add device to active list
            active_list[payload['id']] = payload

            # Send approval to the node
            payload = json.dumps({'action':'approved'}).encode('utf-8')
            self.request.send(payload)

            # If interactive load exceed the limit, turn of background load
            if current_power > threshold:
                if (len(background_list) > 0):
                    pass
                    # find the background load that should be turned off

        # Background load with time interval
        elif (details['flexible'] == 1):
            print('Background 1')
            active_list[payload['id']] = payload

            payload = json.dumps({'action':'approved'}).encode('utf-8')
            self.request.send(payload)

        # Background load with deadline
        elif (details['flexible'] == 2):
            print('Background 2')
            active_list[payload['id']] = payload

            payload = json.dumps({'action':'approved'}).encode('utf-8')
            self.request.send(payload)

            # Check if we have enough power left in order to turn the device on
            if (current_power + details['power'] <= threshold):
                pass
                #current_power += details['power']
                #payload = json.dumps({'action':'approved'}).encode('utf-8')
                #self.request.send(payload)
                
            # Put it in the waiting queue since we don't have priorities yet
            else:
                pass
                #waiting_list[payload['id']] = payload

        # Invalid flexible type
        else:
            print('Invalid flexible type')

    def handle_disconnect(self, payload):
        print('Disconnect from node: ' + str(payload['id']))
        active_list.pop(payload['id'])
        print(active_list)
        payload = json.dumps({'action':'disconnect'}).encode('utf-8')
        self.request.send(payload)

    def handle_update(self, payload):
        print('Update from node: ' + str(payload['id']))

class SmartMeter():
    def __init__(self):
        self.update_price()
        self.find_chepeast_hour()

    def update_price(self):
        self.pricelist = download_price.downloadPrice("elspot_prices.xls")

    # Find cheapest hour and return hour and price for that
    def find_chepeast_hour(self):
        # Should consider if there are several hours with same lowest price, which one has least schedule?
        
        lowest_price = (min(self.pricelist.items(), key=lambda x: x[1]))
        # print ("Hour: " + str(lowest[0]) + " is chepeast, " + str(lowest[1]) + "kr/kWh")
        return lowest_price
    

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    # Host info
    HOST, PORT = "localhost", 9000

    smart_meter = SmartMeter()

    # Create the server
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    server.allow_reuse_address = True

    # Start a server thread to handle incoming connections
    server_thread = threading.Thread(target=server.serve_forever)

    # Set it as a daemon, so it terminates when the Python program ends
    server_thread.daemon = True

    # Start the server
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)
    
    # Infinite loop until we crash
    while True:
        pass
