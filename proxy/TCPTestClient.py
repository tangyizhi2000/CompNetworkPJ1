from socket import *
import sys

if __name__ == '__main__':
    serverName = 'localhost'
    serverPort = 11000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))
    message = input('Input sentence: ')
    clientSocket.send(message.encode())
    modifiedSentence = clientSocket.recv(2048)
    print('From Server: ' +  modifiedSentence.decode())
    clientSocket.close()
