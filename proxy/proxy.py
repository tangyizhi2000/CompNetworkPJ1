#!/usr/bin/env python3.10

from collections import defaultdict
from threading import Thread
from socket import *
import sys
import time
import re

max_num_connections = 10
total_num_connections = 0
mpd_xml = ""
alpha = 0
T_current = defaultdict(lambda: -1)
bitrate_list = []
log_list = []
file_path = None

# record time and send message
# after timing ts and tf, we can update the bandwidth prediction
def time_and_send(serverSocket, client_message, video_chunk, client_IP, server_IP, ts):
    send_to_end(serverSocket, client_message)
    status, response = receive_from_end(serverSocket)
    tf = time.time()
    # calculate throughput, T = B / (tf-ts)
    if video_chunk:
        calculate_throughput(len(response), tf, ts, client_IP, server_IP)
    return status, response

def calculate_throughput(size, tf, ts, client_IP, server_IP):
    global T_current, alpha, log_list
    T = float(size / (tf - ts))
    if T_current[(client_IP, server_IP)] == -1:
        T_current[(client_IP, server_IP)] = bitrate_list[0]
    else:
        T_current[(client_IP, server_IP)] = alpha * T + (1 - alpha) * T_current[(client_IP, web_server_ip)]
    log_list.append(str(time.time()) + " " + str(tf - ts) + " " + str(T) + " " + str(T_current[(client_IP, web_server_ip)]))

# send a message to the target socket
def send_to_end(endSocket, message):
    endSocket.send(message)

def parse_mpd():
    global bitrate_list
    bitrate_loc = mpd_xml.find('bandwidth=\"', 0, len(mpd_xml))
    while bitrate_loc != -1:
        cur_bitrate = 0
        for i in range(bitrate_loc, bitrate_loc + 20):
            if mpd_xml[i].isnumeric():
                cur_bitrate = cur_bitrate * 10 + int(mpd_xml[i])
        bitrate_list.append(cur_bitrate)
        bitrate_loc = mpd_xml.find('bandwidth=\"', bitrate_loc + 10, len(mpd_xml))    
    bitrate_list.sort()

def choose_bitrate(client_IP, web_server_ip):
    for bitrate in reversed(bitrate_list):
        if bitrate < T_current[(client_IP, web_server_ip)] / 1.5:
            return bitrate
    return bitrate_list[0]

'''
BigBuckBunny_6s.mpd
<?xml version="1.0" encoding="UTF-8"?>
<!-- MPD file Generated with GPAC version 0.5.1-DEV-rev5379  on 2014-09-10T13:35:49Z-->
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" minBufferTime="PT1.500000S" type="static" mediaPresentationDuration="PT0H9M56.46S" profiles="urn:mpeg:dash:profile:isoff-live:2011">
  <ProgramInformation moreInformationURL="http://gpac.sourceforge.net">
    <Title>dashed/BigBuckBunny_6s_simple_2014_05_09.mpd generated by GPAC</Title>
  </ProgramInformation>
  <Period duration="PT0H9M56.46S">
    <AdaptationSet segmentAlignment="true" group="1" maxWidth="480" maxHeight="360" maxFrameRate="24" par="4:3">
      <SegmentTemplate timescale="96" media="bunny_$Bandwidth$bps/BigBuckBunny_6s$Number$.m4s" startNumber="1" duration="576" initialization="bunny_$Bandwidth$bps/BigBuckBunny_6s_init.mp4" />
      <Representation id="320x240 46.0kbps" mimeType="video/mp4" codecs="avc1.42c00d" width="320" height="240" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="45514" />
      <Representation id="480x360 177.0kbps" mimeType="video/mp4" codecs="avc1.42c015" width="480" height="360" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="176827" />
      <Representation id="854x480 506.0kbps" mimeType="video/mp4" codecs="avc1.42c01e" width="854" height="480" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="506300" />
      <Representation id="1280x720 1.0Mbps" mimeType="video/mp4" codecs="avc1.42c01f" width="1280" height="720" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="1006743" />
    </AdaptationSet>
  </Period>
</MPD>
BigBuckBunny_6s_nolist.mpd
<?xml version="1.0" encoding="UTF-8"?>
<!-- MPD file Generated with GPAC version 0.5.1-DEV-rev5379  on 2014-09-10T13:35:49Z-->
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" minBufferTime="PT1.500000S" type="static" mediaPresentationDuration="PT0H9M56.46S" profiles="urn:mpeg:dash:profile:isoff-live:2011">
  <ProgramInformation moreInformationURL="http://gpac.sourceforge.net">
    <Title>dashed/BigBuckBunny_6s_simple_2014_05_09.mpd generated by GPAC</Title>
  </ProgramInformation>
  <Period duration="PT0H9M56.46S">
    <AdaptationSet segmentAlignment="true" group="1" maxWidth="480" maxHeight="360" maxFrameRate="24" par="4:3">
      <SegmentTemplate timescale="96" media="bunny_$Bandwidth$bps/BigBuckBunny_6s$Number$.m4s" startNumber="1" duration="576" initialization="bunny_$Bandwidth$bps/BigBuckBunny_6s_init.mp4" />
      <Representation id="1280x720 1.0Mbps" mimeType="video/mp4" codecs="avc1.42c01f" width="1280" height="720" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="1006743" />
    </AdaptationSet>
  </Period>
</MPD>
'''
def handle_mpd(client_messages, serverSocket, client_IP, server_IP, ts):
    # request a copy of mpd.xml
    status1, mpd_file = time_and_send(serverSocket, client_messages, False, client_IP, server_IP, ts)
    global mpd_xml
    mpd_xml = mpd_file.decode()
    parse_mpd()
    # replace 'BigBuckBunny_6s.mpd' with 'BigBuckBunny_6s_nolist.mpd' and request server a copy of it
    mpd_nolist_request = client_messages.replace(b'BigBuckBunny_6s.mpd', b'BigBuckBunny_6s_nolist.mpd')
    status2, mpd_no_list_file = time_and_send(serverSocket, mpd_nolist_request, False, client_IP, server_IP, ts)
    # status is whether server disconnects; mpd_no_list_file is the thing we need to return
    return status1 and status2, mpd_no_list_file

def handle_video_request(client_messages, client_IP, web_server_ip):
    # parse the client request, and request for appropriate video according to throughput
    decode_message = client_messages.decode()
    # find the client requested bitrate
    info_loc = decode_message.find('/bunny_') + len('/bunny_')
    requested_bitrate = ""
    for i in range(info_loc, info_loc + 20):
        if decode_message[i].isnumeric():
            requested_bitrate += decode_message[i]
        else:
            break
    # find appropriate bitrate
    actual_bitrate = choose_bitrate(client_IP, web_server_ip)
    # replace client's request with the appropriate bitrate
    client_messages = client_messages.replace(str(requested_bitrate).encode(), str(actual_bitrate).encode())
    return client_messages, actual_bitrate


def extract_content_length(temp_header):
    content_length = ""
    length_loc = temp_header.find('Content-Length') + len('Content-Length')
    for i in range(length_loc + 2, min(length_loc + 10, len(temp_header))):
        if temp_header[i] == ' ':
            continue
        if temp_header[i].isnumeric():
            content_length += temp_header[i]
        else:
            break
    content_length = int(content_length)
    return content_length

# receive from a socket
# if the message is empty, there is a disconnection
def receive_from_end(endSocket):
    temp_message = endSocket.recv(2048)
    if temp_message == b'':
        return (False, temp_message)
    elif b'Content-Length' not in temp_message:
        return (True, temp_message)
    else:
        all_message = temp_message
        # what is header v.s. what is content
        end_of_header = temp_message.find(b'\r\n\r\n') + len(b'\r\n\r\n')
        temp_header = temp_message[:end_of_header].decode('utf-8', 'ignore')
        content_length = extract_content_length(temp_header) - (len(temp_message) - len(temp_message[:end_of_header]))
        content_length_cp = content_length
        while content_length > 0:
            temp_message = endSocket.recv(content_length_cp)
            content_length = content_length - len(temp_message)
            all_message = all_message + temp_message
        return (True, all_message)


def connect(clientSocket, fake_ip, web_server_ip, addr):
    # Establish a connection with a server
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((fake_ip, 0)) # Socket bind to fake_ip and OS will pick one port
    serverSocket.connect((web_server_ip, 8080)) # connect to the server
    while True:
        # receive from client
        status, client_messages = receive_from_end(clientSocket)
        # timing
        ts = time.time()
        if not status:
            break
        # MPD file request, save the MPD file
        if b'BigBuckBunny_6s.mpd' in client_messages:
            status, mpd_no_list_file = handle_mpd(client_messages, serverSocket, addr[0], web_server_ip)
            if not status:
                break
            send_to_end(clientSocket, mpd_no_list_file)
            #print("HANDLE MPD")
        elif b'bps/BigBuckBunny_6s' in client_messages:
            client_messages, actual_bitrate = handle_video_request(client_messages, addr[0], web_server_ip)
            status, response = time_and_send(serverSocket, client_messages, True, addr[0], web_server_ip, ts)
            # logging /bunny_1006743bps/BigBuckBunny_6s_(init|[0-9]).mp4
            actual_chunk_name = re.findall('[.]*/bunny_[0-9]*bps/BigBuckBunny_6s[0-9]+\.m4s', client_messages.decode())
            global log_list
            log_list[len(log_list)-1] += " " + str(int(actual_bitrate/1000)) + " " + str(web_server_ip) 
            if len(actual_chunk_name) == 1:
                log_list[len(log_list)-1] += " " + str(actual_chunk_name[0]) + "\n"
                # a log file we can write to
                log_file = open(file_path, 'a')
                log_file.write(str(log_list[-1]))
                log_file.close()
                print(log_list[-1])
            if not status:
                break
            send_to_end(clientSocket, response)
            #print("HANDLE PROXYING REQUEST")
        else:
            # send to server
            #print("HANDLE OTHERS MESSAGES")
            send_to_end(serverSocket, client_messages)
            # receive from server
            status, server_response = receive_from_end(serverSocket)
            if not status:
                break
            # send back to client
            send_to_end(clientSocket, server_response)

    # close the relevant connections
    clientSocket.close()
    serverSocket.close()
        


if __name__ == '__main__':
    # commandline ./proxy <log> <alpha> <listen-port> <fake-ip> <web-server-ip>
    file_path, alpha, listen_port, fake_ip, web_server_ip = str(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
    recvSocket = socket(AF_INET,SOCK_STREAM) ## create socket listening for requests from client
    recvSocket.bind(('', listen_port)) # Reachable by any address on port listen_port
    recvSocket.listen(1) # TODO: what is the maximum concurrent connections allowed?
    # Establish a connection with clients
    # allow multiple clients to connect concurrently as long as the total number of clents are less than maximum
    while True:
        # Receive a connection from client
        clientSocket, addr = recvSocket.accept()
        worker = Thread(target=connect, args=(clientSocket, fake_ip, web_server_ip, addr))
        worker.start()