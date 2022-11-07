from threading import Thread
from socket import *
import sys
import time

max_num_connections = 10
total_num_connections = 0
mpd_xml = ""
alpha = 0
T_current = -1
T_current_list = []
bitrate_list = []

# record time and send message
# after timing ts and tf, we can update the bandwidth prediction
def time_and_send(serverSocket, client_message, load):
    ts = time.time()
    send_to_end(serverSocket, client_message)
    status, response = receive_from_end(serverSocket, load)
    tf = time.time()
    # calculate throughput, T = B / (tf-ts)
    calculate_throughput(sys.getsizeof(response), tf, ts)
    return status, response

def calculate_throughput(size, tf, ts):
    global T_current, alpha, T_current_list
    if T_current == -1 and len(bitrate_list) > 1:
        T_current = bitrate_list[0]
    T = float((size - sys.getsizeof(b'')) / (tf - ts))
    T_current = alpha * T - (1 - alpha) * T_current
    T_current_list.append(T_current)

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

def choose_bitrate(requested_bitrate):
    for bitrate in reversed(bitrate_list):
        if bitrate < requested_bitrate / 1.5:
            return bitrate

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
def handle_mpd(client_messages, serverSocket):
    # request a copy of mpd.xml
    status1, mpd_file = time_and_send(serverSocket, client_messages, 2048)
    global mpd_xml
    mpd_xml = mpd_file.decode()
    parse_mpd()
    # replace 'BigBuckBunny_6s.mpd' with 'BigBuckBunny_6s_nolist.mpd' and request server a copy of it
    mpd_nolist_request = client_messages.replace(b'BigBuckBunny_6s.mpd', b'BigBuckBunny_6s_nolist.mpd')
    status2, mpd_no_list_file = time_and_send(serverSocket, mpd_nolist_request, 2048)
    # status is whether server disconnects; mpd_no_list_file is the thing we need to return
    return status1 and status2, mpd_no_list_file

def handle_video_request(client_messages):
    # parse the client request, and request for appropriate video according to throughput
    decode_message = client_messages.decode()
    # find the client requested bitrate
    info_loc = decode_message.find('/bunny_')
    requested_bitrate = ""
    for i in range(info_loc, info_loc + 20):
        if decode_message[i].isnumeric():
            requested_bitrate += decode_message[i]
    # find appropriate bitrate
    actual_bitrate = choose_bitrate(int(requested_bitrate))
    # replace client's request with the appropriate bitrate
    client_messages.replace(requested_bitrate.encode(), str(actual_bitrate).encode())
    return client_messages, actual_bitrate

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
        # Establish a connection with a server
        serverSocket = socket(AF_INET, SOCK_STREAM)
        serverSocket.bind((fake_ip, 0)) # Socket bind to fake_ip and OS will pick one port
        serverSocket.connect((web_server_ip, 8080)) # connect to the server
        while True:
            # receive from client
            status, client_messages = receive_from_end(clientSocket, 2048)
            if not status:
                break
            # MPD file request, save the MPD file
            if b'BigBuckBunny_6s.mpd' in client_messages:
                status, mpd_no_list_file = handle_mpd(client_messages, serverSocket)
                if not status:
                    break
                send_to_end(clientSocket, mpd_no_list_file)
            elif b'bps/BigBuckBunny_6s' in client_messages:
                client_messages, bitrate = handle_video_request(client_messages)
                status, response = time_and_send(serverSocket, client_messages, bitrate * 10)
                print("--------------------------------")
                print("Video Response:", bitrate)
                print("--------------------------------")
                if not status:
                    break
                send_to_end(clientSocket, response)
            else:
                print("--------------------------------")
                print("client message:", client_messages)
                print("--------------------------------")
                # send to server
                send_to_end(serverSocket, client_messages)
                # receive from server
                status, server_response = receive_from_end(serverSocket, 10067431)
                if not status:
                    break
                print("--------------------------------")
                print("server response:", server_response)
                print("--------------------------------")
                # send back to client
                send_to_end(clientSocket, server_response)
                
        # close the relevant connections
        clientSocket.close()
        serverSocket.close()


if __name__ == '__main__':
    # commandline ./proxy <log> <alpha> <listen-port> <fake-ip> <web-server-ip>
    file_path, alpha, listen_port, fake_ip, web_server_ip = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
    recvSocket = socket(AF_INET,SOCK_STREAM) ## create socket listening for requests from client
    recvSocket.bind(('', listen_port)) # Reachable by any address on port listen_port
    recvSocket.listen(max_num_connections) # TODO: what is the maximum concurrent connections allowed?
    # Establish a connection with clients
    # allow multiple clients to connect concurrently as long as the total number of clents are less than maximum
    for i in range(max_num_connections):
        worker = Thread(target=connect, args=(recvSocket, fake_ip, web_server_ip))
        worker.start()