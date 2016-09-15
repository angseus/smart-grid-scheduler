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

    

class Node():
	def __init__(self, id, power, time, flexible, category, priority, group_id):
		# Connect to the Smart Meter
		HOST, PORT = "localhost", 9999
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((HOST, PORT))

		self.id = id
		self.power = power
		self.time = time
		self.flexible = flexible
		self.category = category
		self.priority = priority
		self.group_id = group_id

		register_data = {"id":self.id, "power":self.power, "time":self.time, "flexible":self.flexible,
			"category":self.category, "priority":self.priority, "group_id":self.group_id}

		data = {"action": "register", "payload":register_data}
		# Convert to JSON and send
		data = json.dumps(data).encode('utf-8')
		self.sock.sendall(data)


if __name__ == "__main__":
	node = Node(0, 400, 0, 0, 0, 0, 1)