# Should include
#   - Algorithm
#   - Communication between all nodes
#   - Polling price from NordPool

# May have this structures:
#   - WaitingList = {id, time, power, (group id), deadline}
#   - Price = {Hour, avg price}


import socketserver
import json
import socket
import threading

node_list = {}
waiting_list = {}
active_list = {}
background_list = {}
current_power = 0
threshold = 1500

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
        # Add the node to the list of all nodes
        print('Register from node: ' + str(payload['id']))
        node_list[payload['id']] = payload['details']

        # Check if the node is a background task
        if (payload['details']['flexible'] == 1):
            background_list[payload['id']] = payload['details']

    def handle_request(self, payload):
        print('Request from node: ' + str(payload['id']))
        # Check if we have enough power left in order to turn the device on
        if (current_power <= threshold):
            active_list[payload['id']] = payload
            print (active_list)
            payload = json.dumps({'action':'approved'}).encode('utf-8')
            self.request.send(payload)
        
        # Put it in the waiting queue since we don't have priorities yet
        else:
            waiting_list[payload['id']] = payload
            print (waiting_list)

    def handle_disconnect(self, payload):
        print('Disconnect from node: ' + str(payload['id']))
        active_list.pop(payload['id'])
        print(active_list)
        payload = json.dumps({'action':'disconnect'}).encode('utf-8')
        self.request.send(payload)

    def handle_update(self, payload):
        print('Update from node: ' + str(payload['id']))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 9000

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    server.allow_reuse_address = True

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)
    
    while True:
        pass
