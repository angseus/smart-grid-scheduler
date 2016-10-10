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
from threading import Thread
import time

HOST, PORT = 'localhost', 9000

class Node(Thread):
    def __init__(self, id, power, time, flexible, category, priority, group_id, deadline, activity):
        # Set up threading
        Thread.__init__(self)
        self.daemon = True

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
        self.deadline = deadline
        self.group_id = group_id
        self.activity = activity
        self.block_per_hour = 6

        self.data = {'id':self.id, 'details':{'power':power, 'time':time, 'flexible':flexible,
            'category':category, 'priority':priority, 'group_id':group_id, 'deadline':deadline}}

        payload = {'action': 'register', 'payload':self.data}

        self.send(payload)

        # Start the thread
        self.start()
        
    def update(self):
        payload = {'action':'update', 'payload':self.data}
        self.send(payload)

    def request(self):
        payload = {'action':'request', 'payload':{'id':self.id}}
        self.send(payload)

    def change_load(self, power):
        self.power = power
        self.data['details']['power'] = power
        self.update()

    def disconnect(self):
        payload = {'action':'disconnect', 'payload':{'id':self.id}}
        self.send(payload)

    def send(self, payload):
        payload = json.dumps(payload).encode('utf-8')
        self.sock.sendall(payload)

    def thread_print(self, msg):
        print("Node: " + str(self.id) + ", msg: " + str(msg))

    def handle_recv(self):
        try:
            data = self.sock.recv(1024)
        except Exception as e:
            return

        if not data:
            return
        data = data.decode('utf-8')
        res = []
        try:
            data = data.split('}')
            for part in data:
                if part:
                    part = part + '}'
                    part = json.loads(part)
                    res.append(part)
                else:
                    continue  
        except Exception as e:
            self.thread_print(e)
            return

        return res

    def check_msg(self):
        data = self.handle_recv()
        if data:
            pass
        else:
            return

        self.thread_print(data)
        for action in data:
            self.handle_action(action)

    def handle_action(self, data):
        
        # Check if our request was approved
        if (data['action'] == 'approved'):
            self.switch_on() 

        # Check if we should perform our background activity now
        elif (data['action'] == 'activate'):
            self.switch_on()

        # Check if we should disconnect
        elif (data['action'] == 'disconnect'):
            self.switch_off()
        
        # Invalid
        else:
            self.thread_print (data)
            raise Exception

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
        print("Node: " + str(self.id) + " is alive")
        #index = 16*self.block_per_hour # start at 16 pm instead of middle of night
        index = 0
        current_second = int(time.strftime('%S', time.gmtime()))

        # Run as long as the nodes has simulated activities
        while(index < len(self.activity)):
            
            # If we are flexible we only want to check messages, otherwise check activity list
            self.check_msg()
            if (self.flexible != 1):
                if (current_second != int(time.strftime('%S', time.gmtime()))):
                    self.handle_activity(self.activity[index])
                    index += 1
                    #index = index % (self.block_per_hour*24)
                    current_second = int(time.strftime('%S', time.gmtime()))
        print("Node Done")

if __name__ == '__main__':
    # id, power, time, flexible, category, priority, group_id, deadline, activity
    # Array that tell the node when and how long to request power
    activity0 = [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,2,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,0]
    activity1 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    activity2 = [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    activity3 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,2,0,0,0,0,0,1,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,0]
    activity4 = [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,2,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,0]
    activity5 = [0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,0,0,1,0,0,0,2,0,0,0,0,0,0,0,0,0,1,0,0,0,2,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,2,0,0,0,0,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,0]
    
    # Create the nodes, time should always be based on 6 (one hour)
    # id, power, time,      flexible, category, priority, group_id, deadline, activity
    node0 = Node(0, 600, 0, 0, 1, 0, 1, 0, activity0) # TV
    node1 = Node(1, 120, 2, 2, 1, 0, 1, 17, activity1) # Computer
    node2 = Node(2, 100, 4, 2, 1, 0, 1, 23, activity2) # Derp
    node3 = Node(3, 400, 2, 1, 1, 0, 1, 0, activity3) # TV
    node4 = Node(4, 600, 1, 1, 1, 0, 1, 0, activity4) # TV
    node5 = Node(5, 150, 0, 0, 1, 0, 1, 0, activity5) # TV
    
    
    while True:
        pass
