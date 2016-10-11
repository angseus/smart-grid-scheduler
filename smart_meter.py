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
import matplotlib.pyplot as plt

class SmartMeter():
    def __init__(self):
        # Fetch electricity price for the following 24 hours
        self.pricelist = self.fetch_pricelist()
        self.next_pricelist = self.fetch_pricelist() # This should be different from the first one

        # Start the server
        HOST, PORT = "localhost", 9000
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(10)
        self.sockets = {}
        print ("Listening on port: " + str(PORT))

        # Scheduling variables
        self.node_list = {} # Dict with all known devices
        self.waiting_list = {} # Dict with all waiting background loads
        self.active_list = {} # Dict with all active devices
        self.background_list = {} # Dict with all known background devices(active and inactive)
        self.background_load = {} # Dict with all active background devices
        self.deadline_load = {} # Dict with all active deadline tasks
        self.current_power = 200 # start with an actual background load, just to make data more nice to plot
        self.threshold = 1000  # maximum allowed power
        self.blocks_per_hour = 6 # Set how many blocks there is per hour
        self.clock = 0 #self.blocks_per_hour*16 # Start at 16 a clock
        self.current_hour = 0 # Keeps track of the current hour of the day
        self.block_schedule = self.block_schedule = [[]] * (self.blocks_per_hour * 24) # Schedule for all blocks during 1 day
        
    ###########################################################################
    # Price functions                                                         #
    ###########################################################################
    """
    Fetch a pricelist.
    """
    def fetch_pricelist(self):
        return download_price.downloadPrice("elspot_prices.xls")

    """
    Update the pricelist every hour.
    """
    def update_pricelist(self, current_hour):
        self.pricelist[current_hour-1] = self.next_pricelist[current_hour-1]

    """
    Calculate the total price if we would have started now instead of 
    scheduling it.
    """
    def calculate_worstcase_price(self, duration, power):
        total_price = 0

        index = self.current_hour
        stop = (self.current_hour + duration) % 24
        
        # Make it to kW instead of Watt since price is per kWh
        power = power / 1000

        # Calculate total price from current hour and so many hours the device need to run
        while (index != stop):
            total_price += (self.pricelist[index] * power) 

        return total_price

    ###########################################################################
    # Scheduling a task with deadline                                         #
    ###########################################################################
    """
    Find the cheapest hour in the pricelist. 
    Should maybe consider how much power that is scheduled to that hour already?
    Could be used if there are blocks with the same price. 
    """
    def find_cheapest_hour(self):
        
        lowest_price = (min(self.pricelist.items(), key=lambda x: x[1]))
        # print ("Hour: " + str(lowest[0]) + " is chepeast, " + str(lowest[1]) + "kr/kWh")
        return lowest_price
    
    """
    Find hours between start and deadline (length of duration blocks) with the best price.
    """
    def find_hours(self, duration, deadline):
        valid_hours = [] # This is a list with valid hours (used in order to check the upcoming day)
        hours = [] # This is a list of all the hours that have been chosen
        start = self.current_hour + 1 
        # Create a list with all valid hours
        while (start != deadline):
            valid_hours.append(start)
            # Increase by one and modulo 24 to catch cases where deadline is lower than starttime
            start += 1
            start = start % 24

        for i in range(0, duration):
            cheapest_price = 1000.0
            # Pick out the hour with cheapest price and fulfill the requirements
            for k, v in self.pricelist.items():
                if ((k not in hours) and (k in valid_hours)):
                    if (v < cheapest_price):
                        cheapest_price = v
                        hour = k
            hours.append(hour)

        return hours
        
    """
    Schedule a task with a deadline.
    """
    def schedule_deadline_task(self, node_id, deadline, duration):
        
        print(self.pricelist)

        # TODO: Should it include power as well? Checking threshold and so on
        hours = self.find_hours(duration, deadline)
        print("hours = " + str(hours))

        power = self.node_list[node_id]['power']
        print("power : " + str(power))

        # Add the power consumption for each block of the best suitable hours
        for h in hours:
            # Find the blocks representing each hour
            index = h * self.blocks_per_hour
            for i in range(index, (index + self.blocks_per_hour)):
                # Add id and power to that index in the list, id to be able to 
                # call it later when it should be activated

                self.block_schedule[i].append(({'id' : node_id, 'power': power}))
                #item for item in self.block_schedule if item[0] == id

        print("Node " + str(node_id) + " scheduled!")




    """
    Check if there is a scheduled task that should be started this block.
    """
    def check_scheduled_tasks(self):
        # Get which block in the schedule list we should look at
        # Go through all tasks in the block schedule and see if some of them not is 
        # active, then we know it should be started now
        for node in self.block_schedule[self.clock]:
            
            # v could looks like [{1:300}, {2:500}]  should check if id:s is in active list already
            if node['id'] not in self.active_list:
                print("ID not in active list, should start it now instead")
                # Send activate message
                payload = json.dumps({'action':'activate'}).encode('utf-8')
                self.sockets[node['id']].send(payload)

                # Add device to lists that keep track of the active ones
                self.active_list[node['id']] = {'id': node['id']}
                self.deadline_load[node['id']] = {'id': node['id']}

                # add power to current_power as well
                self.current_power += node['power']

    ###########################################################################
    # Background / Interactive Scheduling                                     #
    ###########################################################################
    """
    Helpfunction that help finding the best background load to pause
    with the shortest time left, since it is easier to schedule it later.
    """
    def find_least_slack(self, temp_list):
        # Sort by lowest time block left, and if same, sort by lowest power
        if (len(temp_list) > 0):
            # slack = 6 means run 6/6 blocks/hour, meaning maximum and no scheduable
            slack = self.blocks_per_hour
            
            # Temporary list that keeps track of nodes with identical values
            tmp_list = {}

            # Find minimum time
            for k, v in temp_list.items():
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
                        val = v
                        break    
            else:
                val = tmp_list[node_id]

            #print(str(node_id) + " has the highest slack")
            return node_id, val
        
        # If no backgroundloads exists, send back a message for that
        else:
            return None, None

    """
    Start a background load if the threshold is okay. 
    Also check if a background load MUST be started
    in order to make it this hour. 
    """
    def schedule_background(self, clock):
        activate_list = []

        # Check if there are any loads that have to be turned on this round
        if (self.waiting_list):
            time_left = self.blocks_per_hour - clock
            for k, v in self.waiting_list.items():
                if (v['time'] == time_left):
                    print("Turn on emergency background for node: " + str(k))
                    # Send activate msg to the background node
                    payload = json.dumps({'action':'approved'}).encode('utf-8')
                    self.sockets[k].send(payload)
                    
                    # Update current power
                    self.current_power += v['power']

                    # Add it to the active list and remove it from waiting list
                    self.active_list[k] = {'id': k}                   

                    # Add it to background loads to be able to see active backgrounds
                    self.background_load[k] = v

                    # add id:s to a temporary list since you can't change size of the list you iterate over
                    activate_list.append(k)
            
            # Remove all loads that are started 
            for k in activate_list:
                self.waiting_list.pop(k)

            while ((self.current_power < self.threshold) and self.waiting_list):
                # find the background node that should be turned off
                node_id, node_details = self.find_least_slack(self.waiting_list)
                print("Should turn on " + str(node_id))
                
                # Send activate msg to the background node
                payload = json.dumps({'action':'approved'}).encode('utf-8')
                self.sockets[node_id].send(payload)
                
                # Update current power
                self.current_power += node_details['power']

                # Add it to the active list and remove it from waiting list
                self.active_list[node_id] = {'id': node_id}
                self.waiting_list.pop(node_id)

                # Add it to background loads to be able to see active backgrounds
                self.background_load[node_id] = node_details
            else:
                print("Uses to much power to enable background")
    
    """
    Function that runs every hour in order to reset background loads.
    """
    def reset_backgrounds(self):
        # Loop through all background devices and reset the time
        for k, v in self.background_list.items():
            v['time'] = self.node_list[k]['time']
            self.background_list.update({k: v})

        # If we miss someone, should throw error or empty the list
        if ((len(self.waiting_list) != 0) or (len(self.background_load) != 0)):
            # Remove all background loads from active list
            for k, v in self.background_list.items():
                try:
                    self.active_list.pop(k)
                    self.current_power -= self.node_list[k]['power']
                except:
                    continue

            self.waiting_list.clear()
            self.background_load.clear()
            print("Opps! Missed to schedule some background loads")

        # Add all reset items to the list again
        for k, v in self.background_list.items():
            self.waiting_list[k] = v

    ###########################################################################
    # General Helper functions                                                #
    ###########################################################################
    """
    We want to change to the next block. Decrease the remaining 
    time of all background loads with 1 and check if we should disconnect
    a scheduled task for now. The scheduled task might be finished, otherwise
    it will be started another block. 
    """
    def decrease_time(self):
        disconnect_list = []

        # If it is a background task
        if (self.background_load):
            for k, v in self.background_load.items():
                v['time'] = v['time'] - 1
                
                # If time is 0, disconnect the device
                if (v['time'] == 0):
                    print(str(k) + " is done for this hour")
                    # Send disconnect msg to the background node
                    payload = json.dumps({'action':'disconnect'}).encode('utf-8')
                    self.sockets[k].send(payload)
                    
                    self.current_power -= v['power']
                    self.active_list.pop(k)

                    # add id:s to a temporary list since you can't change size of the list you iterate over
                    disconnect_list.append(k)
            
            # Remove all loads that are done 
            for k in disconnect_list:
                self.background_load.pop(k)

        # If it is a deadline task
        if (self.deadline_load):

            # Get all scheduled task next hour
            next_step = self.block_schedule[self.clock+1]

            for node in self.block_schedule[self.clock]:
                if ((node['id'] in self.active_list) and (node not in next_step)):
                    
                    payload = json.dumps({'action':'disconnect'}).encode('utf-8')
                    self.sockets[node['id']].send(payload)
                    
                    self.current_power -= self.node_list[node['id']]['power']
                    self.active_list.pop(node['id'])
                    self.deadline_load.pop(node['id'])

    ###########################################################################
    # Communication and handle helpers                                        #
    ###########################################################################
    """
    Register a node. Save neccesary information about it.
    """
    def handle_register(self, payload):

        # Add the node to the list of all nodes
        print('Register from node: ' + str(payload['id']))
        self.node_list[payload['id']] = payload['details'].copy()
        id = payload['id']
        
        # Check if the node is a background task
        if (payload['details']['flexible'] == 1):
            self.background_list[payload['id']] = payload['details']
            self.waiting_list[payload['id']] = payload['details']

        elif (payload['details']['flexible'] == 2):
            print("Scheduable task")

        return id

    """
    Handle a request from a node. This might be a request 
    to schedule something with a deadline or an interactive
    task that needs to be started right away.
    """
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
            self.active_list[payload['id']] = {'id': payload['id']}

            # Send approval to the node
            payload = json.dumps({'action':'approved'}).encode('utf-8')
            
            self.sockets[id].send(payload)

            # TODO, check so we don't disconnect any emergency load that has to run

            # If interactive load exceed the limit, turn off background load
            if self.current_power > self.threshold:
                # Until we have a current power below threshold, continue
                while (self.current_power > self.threshold):
                    # find the background node that should be turned off
                    node_id, node_details = self.find_least_slack(self.background_load)
                    # Check that there arent any background loads to disconnect
                    if (not node_id):
                        break
                    
                    # Send disconnect msg to the background node
                    payload = json.dumps({'action':'disconnect'}).encode('utf-8')
                    self.sockets[node_id].send(payload)

                    # Remove it from the active list
                    self.active_list.pop(node_id)
                    
                    # Add the device back to the waiting list
                    self.waiting_list[node_id] = node_details

                    # Decrease the power
                    self.current_power -= self.node_list[node_id]['power']
                    self.background_load.pop(node_id)

        # Deadline task
        elif (details['flexible'] == 2):
            print('Schedulable')

            deadline = details['deadline']
            duration = details['time']

            self.schedule_deadline_task(id, deadline, duration)
        else:
            raise Exception

    """
    Disconnect a load. This should not happen except
    for interactive loads.
    """
    def handle_disconnect(self, payload):
        print('Disconnect from node: ' + str(payload['id']))
        id = payload['id']

        self.active_list.pop(id)

        payload = json.dumps({'action':'disconnect'}).encode('utf-8')
        self.sockets[id].send(payload)

        details = self.node_list[id]
        self.current_power -= details['power']

    """
    Update from a node. This is currently not used
    from the node / load since we assume that loads
    does not change during runtime. 
    """
    def handle_update(self, payload):
        print('Update from node: ' + str(payload['id']))

    """
    Helper function for receive
    """
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

    """
    Helper function to handle different incoming 
    actions. Send to the correct helper function for 
    that action.
    """
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

    ###########################################################################
    # Main                                                                    #
    ###########################################################################
    def main(self):
        while True:
            # Always decrease time when we executed one turn in the loop
            self.decrease_time()

            # Fetch current second
            self.current_second = int(time.strftime('%S', time.gmtime()))

            # The scheduler for the background loads
            self.schedule_background((self.clock%self.blocks_per_hour))

            # The scheduler for already scheduled tasks, check if some should be turned on
            self.check_scheduled_tasks()

            print("======== New block ========")
            print("Current power: " + str(self.current_power))
            print("Active list: " + str(self.active_list))
            print("Background load: " + str(self.background_load))
            print("Deadline load: " + str(self.deadline_load))
            print("Waiting list: " + str(self.waiting_list))

            # Wait here until next second
            while(self.current_second == int(time.strftime('%S', time.gmtime()))):

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
                time.sleep(0.4)

            # Increase time
            print("Clock: " + str(self.clock))
            self.clock += 1


            if (self.clock % self.blocks_per_hour == 0):
                print("================== NEW HOUR =================")
                # Increase to new hour and keep it between 0 and 23
                self.current_hour += 1
                self.current_hour = self.current_hour % 24

                # Reset function that reset the internal time for all background devices every 6th block (seconds)
                self.reset_backgrounds()

                # Update pricelist with the last hour
                self.update_pricelist(self.current_hour)

            if (self.clock % (self.blocks_per_hour*24) == 0):
                print("!!!!!!!!!!!!!!!!!! New day! !!!!!!!!!!!!!!!!!!")
            
if __name__ == "__main__":
    smart_meter = SmartMeter()
    smart_meter.main()
