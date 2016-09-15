# Should include
#   - Algorithm
#   - Communication between all nodes
#   - Polling price from NordPool

# May have this structures:
#   - WaitingList = {id, time, power, (group id), deadline}
#   - Price = {Hour, avg price}


import socketserver
import json

node_list = {}
waiting_list = {}
active_list = {}
current_power = 0
threshold = 1500

class RequestHandler(socketserver.BaseRequestHandler):
    """
    The request handler for incoming packages to the server.
    """

    def handle(self):
        while True:
            self.data = self.request.recv(1024)
            if not self.data:
                return
            self.data = self.data.decode('utf-8')
            try:
                self.data = json.loads(self.data)
            except Exception as e:
                print (e)
            print (self.data)

            """
            Depending on the action, perform the proper operation.
            """

            action = self.data["action"]
            payload = self.data["payload"]

            # Register action
            if (action == 'register'):
                self.handle_register(payload)

            # Request action
            elif (action == 'request'):
                self.handle_request(payload)

            elif (action == 'update'):
                self.handle_update(payload)

            elif (action == 'disconnect'):
                self.handle_disconnect(payload)

            # Invalid, drop it 
            else:
                print('Invalid action received')

    def handle_register(self, payload):
        print("Register from node: " + str(payload["id"]))
        node_list[payload["id"]] = payload["details"]

    def handle_request(self, payload):
        print("Request from node: " + str(payload["id"]))
        # Check if we have enough power left in order to turn the device on
        if (current_power <= threshold):
            active_list[payload["id"]] = payload
            print (active_list)
        
        # Put it in the waiting queue since we don't have priorities yet
        else:
            waiting_list[payload["id"]] = payload
            print (waiting_list)

    def handle_disconnect(self, payload):
        print("Disconnect from node: " + str(payload["id"]))
        active_list.pop(payload["id"])
        print(active_list)

    def handle_update(self, payload):
        print("Update from node: " + str(payload["id"]))

class SmartMeter():
    def __init__(self):
        # Server data
        HOST, PORT = "localhost", 9999
        self.server = socketserver.TCPServer((HOST, PORT), RequestHandler)
        self.server.serve_forever()

if __name__ == "__main__":
    smart_meter = SmartMeter()
