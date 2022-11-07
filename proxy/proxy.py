from threading import Thread
from socket import *
import sys
import time

max_num_connections = 10
total_num_connections = 0

# send a message to the target socket
def send_to_end(endSocket, message):
    endSocket.send(message)

# receive from a socket
# detect \n as the end of the message
# if the message is empty, there is a disconnection
def receive_from_end(endSocket, load):
    all_messages = endSocket.recv(load)
    if all_messages == b"":
        return (False, "")
    return (True, all_messages)

def connect(recvSocket, fake_ip, web_server_ip):
    while True:
        # Receive a connection from client
        clientSocket, addr = recvSocket.accept()
        # ts is used to calculate the bandwidth
        ts = time.time()
        # Establish a connection with a server
        serverSocket = socket(AF_INET, SOCK_STREAM)
        serverSocket.bind((fake_ip, 0)) # Socket bind to fake_ip and OS will pick one port
        serverSocket.connect((web_server_ip, 8080)) # connect to the server
        while True:
            # receive from client
            status, client_messages = receive_from_end(clientSocket, 2048)
            if not status:
                break
            if b'BigBuckBunny_6s.mpd' in client_messages:
                print('MPD', client_messages)
            if b'BigBuckBunny_6s' in client_messages:
                print('BigBuckBunny_6s', client_messages)
            print("client message:", client_messages, ts)
            # send to server
            send_to_end(serverSocket, client_messages)
            # receive from server
            status, server_response = receive_from_end(serverSocket, 10067431)
            if not status:
                break
            print("server response:", server_response)
            # send back to client
            send_to_end(clientSocket, server_response)
            
        # close the relevant connections
        clientSocket.close()
        serverSocket.close()


if __name__ == '__main__':
    # commandline ./proxy <log> <alpha> <listen-port> <fake-ip> <web-server-ip>
    file_path, alpha, listen_port, fake_ip, web_server_ip = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
    
    recvSocket = socket(AF_INET,SOCK_STREAM) ## create socket listening for requests from client
    recvSocket.bind(('', listen_port)) # Reachable by any address on port listen_port
    recvSocket.listen(max_num_connections) # TODO: what is the maximum concurrent connections allowed?
    # Establish a connection with clients
    # allow multiple clients to connect concurrently as long as the total number of clents are less than maximum
    for i in range(max_num_connections):
        worker = Thread(target=connect, args=(recvSocket, fake_ip, web_server_ip))
        worker.start()