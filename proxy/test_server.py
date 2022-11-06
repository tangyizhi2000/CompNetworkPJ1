from threading import Thread
from socket import *
import sys
import time

if __name__ == '__main__':
    # commandline ./proxy <log> <alpha> <listen-port> <fake-ip> <web-server-ip>
    file_path, alpha, listen_port, fake_ip, web_server_ip = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
    
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((fake_ip, 0)) # Socket bind to fake_ip and OS will pick one port
    print("OK1")
    serverSocket.connect((web_server_ip, 8080)) # connect to the server
    print("OK2")
    serverSocket.send("messageaa".encode())
    print("OK3")