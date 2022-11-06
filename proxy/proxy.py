from threading import Thread
from socket import *
import sys
import time

max_num_connections = 10
total_num_connections = 0

def connect(recvSocket):
    while True:
        # Receive a connection from client
        connectionSocket, addr = recvSocket.accept()
        # ts is used to calculate the bandwidth
        ts = time.time()
        # Establish a connection with a server
        sendSocket = socket(AF_INET, SOCK_STREAM)
        sendSocket.bind((fake_ip, 0)) # Socket bind to fake_ip and OS will pick one port
        sendSocket.connect((web_server_ip, 8080)) # connect to the server

        message = connectionSocket.recv(2048) 
        capitalizedSentence = message.decode().upper()
        time.sleep(3)
        connectionSocket.send(capitalizedSentence.encode())
        connectionSocket.close()

if __name__ == '__main__':
    # commandline ./proxy <log> <alpha> <listen-port> <fake-ip> <web-server-ip>
    file_path, alpha, listen_port, fake_ip, web_server_ip = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
    
    recvSocket = socket(AF_INET,SOCK_STREAM) ## create socket listening for requests from client
    recvSocket.bind(('', listen_port)) # Reachable by any address on port listen_port
    recvSocket.listen(max_num_connections) # TODO: what is the maximum concurrent connections allowed?
    # Establish a connection with clients
    # allow multiple clients to connect concurrently as long as the total number of clents are less than maximum
    for i in range(max_num_connections):
        worker = Thread(target=connect, args=(recvSocket,))
        worker.start()