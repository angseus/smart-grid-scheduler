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
import time
import select

class SmartMeter():
    def __init__(self):
        # Fetch price
        self.update_price()
        self.find_chepeast_hour()

        # Start the server
        HOST, PORT = "localhost", 9000
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(10)
        self.sockets = {}
        print ("Listening on port: " + str(PORT))

        # Scheduling variables
        self.node_list = {} # Tuple with all known devices
        self.waiting_list = {} # Tuple with all waiting background loads
        self.active_list = {} # Tuple with all active devices
        self.background_list = {} # Tuple with all known background devices(active and inactive)
        self.current_power = 0 
        self.threshold = 1500  # maximum allowed power
        self.pricelist = {} # keeps track of the following days hourly electricaly price
        self.blocks_per_hour = 6 # Set how many blocks there is per hour

    def update_price(self):
        self.pricelist = download_price.downloadPrice("elspot_prices.xls")

    # Find cheapest hour and return hour and price for that
    def find_chepeast_hour(self):
        # Should consider if there are several hours with same lowest price, which one has least schedule?
        
        lowest_price = (min(self.pricelist.items(), key=lambda x: x[1]))
        # print ("Hour: " + str(lowest[0]) + " is chepeast, " + str(lowest[1]) + "kr/kWh")
        return lowest_price

    def handle_register(self, payload):

        # Add the node to the list of all nodes
        print('Register from node: ' + str(payload['id']))
        self.node_list[payload['id']] = payload['details']
        id = payload['id']

        # Check if the node is a background task
        if (payload['details']['flexible'] == 1):
            self.background_list[payload['id']] = payload['details']

        return id

    def find_highest_slack(self):
        # Sort by lowest time block left, and if same, sort by lowest power
        if (len(background_list) > 0):
            # slack = 6 means run 6/6 blocks/hour, meaning maximum and no scheduable
            slack = self.blocks_per_hour
            
            # Temporary list that keeps track of nodes with identical values
            tmp_list = {}

            # Find minimum time
            for k, v in self.background_list.items():
                if (v['time'] < slack):
                    slack = v['time']
                    node_id = k
                    tmp_list = {}
                    tmp_list.update({k: v})
                elif (v['time'] == slack and slack != self.blocks_per_hour):
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
        
        # If no backgroundloads exists, send back a message for that
        else:
            return None


    def handle_request(self, payload):
        print('Request from node: ' + str(payload['id']))
        id = payload['id']
        # Get the tuple of details based on the requested node's id
        details = self.node_list[payload['id']]
        
        # Check which flexibility the node has
        # Interactive load
        if (details['flexible'] == 0):
            print('Interactive load')
            # Add the power to the total consumption
            self.current_power += details['power']
            
            # Add device to active list
            self.active_list[payload['id']] = payload

            # Send approval to the node
            payload = json.dumps({'action':'approved'}).encode('utf-8')
            
            self.sockets[id].send(payload)

            # If interactive load exceed the limit, turn off background load
            if self.current_power > self.threshold:
                while (self.current_power > self.threshold):
                    # find the background node that should be turned off
                    node_id = self.find_highest_slack()
                    if (!node_id):
                        print('No background loads available')
                        break
                    
                    print('in smart_meter, turn off node : ' + str(node_id))
                    # Send disconnect msg to the background node
                    #payload = json.dumps({'action':'disconnect'}).encode('utf-8')
                    #self.request.send(payload)

                    # Decrease the power
                    self.current_power -= self.node_list[node_id]['power']
                    del self.background_list[node_id]

        # Background load with time interval
        elif (details['flexible'] == 1):
            print('Background')
            self.active_list[payload['id']] = payload
            #background_list[payload['id']] = payload # already insert it in register

            self.current_power += details['power']

        # Background load with time interval
        elif (details['flexible'] == 1):
            print('Background 1')
            self.active_list[payload['id']] = payload

            payload = json.dumps({'action':'approved'}).encode('utf-8')
            self.sockets[id].send(payload)

        # Background load with deadline
        elif (details['flexible'] == 2):
            print('Schedulable')
            self.active_list[payload['id']] = payload

            payload = json.dumps({'action':'approved'}).encode('utf-8')
            self.sockets[id].send(payload)

            # Check if we have enough power left in order to turn the device on
            if (self.current_power + details['power'] <= self.threshold):
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
        id = payload['id']

        self.active_list.pop(id)
        print(self.active_list)

        payload = json.dumps({'action':'disconnect'}).encode('utf-8')
        self.sockets[id].send(payload)

    def handle_update(self, payload):
        print('Update from node: ' + str(payload['id']))

    def handle_recv(self, s):
        try:
            data = s.recv(1024)
        except Exception as e:
            return

        if not data:
            return
        data = data.decode('utf-8')
        try:
            data = json.loads(data)
        except Exception as e:
            print (e)
            return

        return data

    def handle_action(self, data):
        action = data['action']
        payload = data['payload']

        # Request action
        if (action == 'request'):
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

    def main(self):
        while True:
            # Check if the main socket has connection
            readable, writable, errored = select.select([self.server_socket], [], [], 0)
            for s in readable:
                if s is self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    data = client_socket.recv(1024)

                    if not data:
                        continue
                    data = data.decode('utf-8')
                    try:
                        data = json.loads(data)
                    except Exception as e:
                        print (e)
                        continue

                    # Set it up
                    # Might need to set up a much higher timeout here as well, AND in node.py sockets
                    client_socket.setblocking(0)

                    # Fetch the id and add it to the socket list
                    id = self.handle_register(data['payload'])
                    self.sockets[id] = client_socket

            # Check if the other sockets have sent something to us
            for s in self.sockets.values():
                data = self.handle_recv(s)
                if data:
                    self.handle_action(data)
                else:
                    continue

            # Sleep for a while! :) 
            time.sleep(0.001)

if __name__ == "__main__":
    # Host info
    smart_meter = SmartMeter()
    smart_meter.main()
