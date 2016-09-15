# Should include
#   - Algorithm
#   - Communication between all nodes
#   - Polling price from NordPool

# May have this structures:
#   - WaitingList = {id, time, power, (group id), deadline}
#   - Price = {Hour, avg price}


import socketserver
import json

node_list = []
waiting_list = []
active_list = []

class RequestHandler(socketserver.BaseRequestHandler):
    """
    The request handler for incoming packages to the server.
    """

    def handle(self):
        self.data = json.loads(self.request.recv(1024).decode('utf-8'))

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

        # Invalid, drop it 
        else:
            print('Invalid action received')

    def handle_register(self, payload):
        node_list.append(payload)
        print (node_list)

class SmartMeter():
    def __init__(self):
        # Server data
        HOST, PORT = "localhost", 9999
        self.server = socketserver.TCPServer((HOST, PORT), RequestHandler)
        self.server.serve_forever()

if __name__ == "__main__":
    smart_meter = SmartMeter()
