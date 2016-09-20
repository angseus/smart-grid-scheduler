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
threshold = 200  # maximum allowed power
pricelist = {} # keeps track of the following days hourly electricaly price
blocks_per_hour = 6 # Set how many blocks there is per hour

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
        global background_list

        # Add the node to the list of all nodes
        print('Register from node: ' + str(payload['id']))
        node_list[payload['id']] = payload['details']

        # Check if the node is a background task
        if (payload['details']['flexible'] == 1):
            background_list[payload['id']] = payload['details']

    def find_highest_slack(self):
        global background_list, blocks_per_hour
        # Sort by lowest time block left, and if same, sort by lowest power
        
        # slack = 6 means run 6/6 blocks/hour, meaning maximum and no scheduable
        slack = blocks_per_hour
        
        # Temporary list that keeps track of nodes with identical values
        tmp_list = {}

        # Find minimum time
        for k, v in background_list.items():
            if (v['time'] < slack):
                slack = v['time']
                node_id = k
                tmp_list = {}
                tmp_list.update({k: v})
            elif (v['time'] == slack and slack != blocks_per_hour):
                tmp_list.update({k: v})

        # Find which node that has lowest power and return it
        if (len(tmp_list) > 1):
            # Infinite high number to make sure no device has higher power
            low_pow = 99999
            # Find minimum power consumption
            for k, v in tmp_list.items():
                if (v['power'] < low_pow):
                    low_pow = v['power']

            for k, v in tmp_list.items():
                if v['power'] == low_pow:
                    node_id = k
                    break
            
        print("Turn off : " + str(node_id))
        return node_id


    def handle_request(self, payload):
        global current_power, threshold, background_list

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

            # If interactive load exceed the limit, turn off background load
            if current_power > threshold:
                while (current_power > threshold):
                    # find the background node that should be turned off
                    node_id = self.find_highest_slack()
                    print('in smart_meter, turn off node : ' + str(node_id))
                    # Send disconnect msg to the background node
                    #payload = json.dumps({'action':'disconnect'}).encode('utf-8')
                    #self.request.send(payload)

                    # Decrease the power
                    current_power -= node_list[node_id]['power']
                    del background_list[node_id]

        # Background load with time interval
        elif (details['flexible'] == 1):
            print('Background')
            active_list[payload['id']] = payload
            #background_list[payload['id']] = payload # already insert it in register

            current_power += details['power']

            payload = json.dumps({'action':'approved'}).encode('utf-8')
            self.request.send(payload)

        # Background load with deadline
        elif (details['flexible'] == 2):
            print('Schedulable')
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
        global current_power

        print('Disconnect from node: ' + str(payload['id']))
        active_list.pop(payload['id'])
        print(active_list)

        # Decrease the power
        #current_power -= node_list[payload['id']]['power']

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
