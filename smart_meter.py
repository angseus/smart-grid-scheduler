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
            self.data = json.loads(self.data)
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

            # Invalid, drop it 
            else:
                print('Invalid action received')

    def handle_register(self, payload):
        print("Register from node: " + str(payload["id"]))
        node_list[payload["id"]] = payload["details"]

    def handle_request(self, payload):
        print("Request update from node: " + str(payload["id"]))

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
