from socket import *
import sys

# send a message to the target socket
def send_to_end(endSocket, message):
    endSocket.send(message.encode())

# receive from a socket
# detect \n as the end of the message
# if the message is empty, there is a disconnection
def receive_from_end(endSocket):
    all_messages = ""
    tmp_massage = ""
    while '\n' not in tmp_massage:
        tmp_massage = endSocket.recv(2048).decode()
        # if the message is empty, there is a disconnection
        if tmp_massage == "":
            return (False, "")
        all_messages += tmp_massage
    all_messages = all_messages[:all_messages.find('\n')+1]
    return (True, all_messages)

if __name__ == '__main__':
    # parse the ports and ip addresses passed into the function
    listen_port, fake_ip, server_ip = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    #print(listen_port, fake_ip, server_ip)
    recvSocket = socket(AF_INET,SOCK_STREAM) ## LISTENING SOCKET
    recvSocket.bind(('', listen_port)) # Reachable by any address on port listen_port
    while True:
        # Establish a connection with a client
        recvSocket.listen(1)
        clientSocket, addr = recvSocket.accept() ## RETURNS CONNECTION SOCKET
        # Establish a connection with a server
        sendSocket = socket(AF_INET, SOCK_STREAM)
        sendSocket.bind((fake_ip, 0)) # Socket bind to fake_ip and OS will pick one port
        sendSocket.connect((server_ip, 8080)) # connect to the server
        while True:
            # receive from client
            status, client_messages = receive_from_end(clientSocket)
            if not status:
                break
            # send to server
            send_to_end(sendSocket, client_messages)
            # receive from server
            status, server_response = receive_from_end(sendSocket)
            if not status:
                break
            # send back to client
            send_to_end(clientSocket, server_response)
        # close the relevant connections
        clientSocket.close()
        sendSocket.close()
