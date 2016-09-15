# Should include
#	- Simulating data for a specific node
# 	- Node = {id, power, time, flexible, category, priority, group id}

# Should have the following variables:
# ID/Name
# Power - Watt
# Time - If battery charge or runtime to heat up the house, how long time to load?
# Flexible - Can you schedule it? 
# ... 0 means interactive loads since we cannot control them at all
# ... 1 means background load that need to be run in a certain interval (slack), 
# ... 2 (extended) means that we have a deadline, but nothing else to consider
# Category
# Priority - How important it is compared to other products
# Group ID (Fas) - Feature to be able to restrict total consumption at the same phase

import socket
import sys
import json
import time

HOST, PORT = "localhost", 9999

class Node():
	def __init__(self, id, power, time, flexible, category, priority, group_id):
		# Connect to the Smart Meter
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((HOST, PORT))
		self.id = id
		self.power = power
		self.time = time
		self.flexible = flexible
		self.category = category
		self.priority = priority
		self.group_id = group_id

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
		print (payload)
		self.sock.sendall(payload)

if __name__ == "__main__":
	node0 = Node(0, 400, 0, 0, 0, 0, 1) # interactive load
	#node1 = Node(1, 600, 0, 0, 0, 0, 1) # interactive load
	#node2 = Node(2, 800, 0, 0, 0, 0, 1) # interactive load
	node0.request()
	time.sleep(2)
	node0.disconnect()
	