# Should include
#   - Simulating data for a specific node
#   - Node = {id, power, time, flexible, category, priority, group id}

# Should have the following variables:
# ID/Name
# Power - Watt
# Time - If battery charge or runtime to heat up the house, how long time to load?
# Flexible - Can you schedule it? 
# ... 0 means interactive loads since we cannot control them at all
# ... 1 means background load that need to be run in a certain interval (slack), 
# ... 2 (extended) means that we have a deadline, but nothing else to consider
# Category - Category of the load
# ... 0 - Heating
# ... 1 - Fridge
# ... 2 - Electronics (TV/Computer etc.)
# ... 3 - Kitchen
# ... 4 - Lights
# ... 5 - Charging
# Priority - How important it is compared to other products
# Group ID (Fas) - Feature to be able to restrict total consumption at the same phase

import socket
import sys
import json
import time
import threading
import time

HOST, PORT = "localhost", 9999

class Node(threading.Thread):
    def __init__(self, id, power, time, flexible, category, priority, group_id, activity):
        threading.Thread.__init__(self)

        # Connect to the Smart Meter
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        self.sock.setblocking(0)
        self.id = id
        self.power = power
        self.time = time
        self.flexible = flexible
        self.category = category
        self.priority = priority
        self.group_id = group_id
        self.activity = activity

        self.data = {"id":self.id, "details":{"power":power, "time":time, "flexible":flexible,
            "category":category, "priority":priority, "group_id":group_id}}

        payload = {"action": "register", "payload":self.data}

        self.send(payload)
        
    def update(self):
        payload = {"action":"update", "payload":self.data}
        self.send(payload)

    def request(self):
        payload = {"action":"request", "payload":{"id":self.id}}
        self.send(payload)

    def change_load(self, power):
        self.power = power
        self.data["details"]["power"] = power
        self.update()

    def disconnect(self):
        payload = {"action":"disconnect", "payload":{"id":self.id}}
        self.send(payload)

    def send(self, payload):
        payload = json.dumps(payload).encode('utf-8')
        self.sock.sendall(payload)

    def check_msg(self):
        try:
            res = self.sock.recv(1024)
        except Exception as e:
            time.sleep(0.001)
            res = ''

        if not res:
            return
        res = res.decode('utf-8')
        try:
            res = json.loads(res)
        except Exception as e:
            print (e)
        
        if (res['action'] == 'approved'):
            self.switch_on() 
        elif (res['action'] == 'disconnect'):
            self.switch_off()
        else:
            pass

    def handle_activity(self, action):
        if (action == 1):
            self.request()
        elif (action == 2):
            self.disconnect()
        elif (action == 0):
            pass
        else:
            raise Exception

    def switch_on(self):
        # Connect PlugWise here
        print('Turning on node: ' + str(self.id))
        pass

    def switch_off(self):
        # Disconnect PlugWise here
        print('Turning off node: ' + str(self.id))
        pass

    def run(self):
        index = 0
        current_second = int(time.strftime("%S", time.gmtime()))
        while(True):
            self.check_msg()
            if (current_second != int(time.strftime("%S", time.gmtime()))):
                self.handle_activity(self.activity[index])
                index += 1
                current_second = int(time.strftime("%S", time.gmtime()))


if __name__ == "__main__":
    # id, power, time, flexible, category, priority, group_id, activity

    # Array that tell the node when and how long to request power
    activity = [0,0,0,0,0,0,1,2,0,0,0,0,0,1,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,2,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,0]

    # Create the nodes
    node0 = Node(0, 400, 0.25, 1, 1, 0, 1, activity) # Fridge, background load
    #node1 = Node(1, 500, 0.5, 1, 0, 0, 1) # Heating, background load

    node0.start()

    
    