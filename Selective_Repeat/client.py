import socket
import sys
import threading
import time
import struct
import random
from queue import *

####################### Function for noting current time #######################	
def current_time():
	return int(round(time.time() * 1000 ))

	
####################### Function to read input file #######################
def file_read(file_name, MSS):
    packet_number = 0
    fin = ''
    try:
        read_file = open(file_name, 'rb')
        data_read = read_file.read(MSS)
        while data_read:
            transfer_data.append(packet_create(data_read, packet_number, data_packet))
            data_read = read_file.read(MSS)
            packet_number = packet_number + 1

        fin = '0'
        fin = fin.encode('utf-8')
        transfer_data.append(packet_create(fin, packet_number, final_packet))
        read_file.close()
        global total_packets
        global track_pkts_ack
        total_packets = len(transfer_data)
        track_pkts_ack = [False] * total_packets
    except (FileNotFoundError, IOError):
        print("Wrong file name or file path")
        exit(1)

		
####################### Function for creating packets #######################			
def packet_create(payload, pkt_no, rcvd_packet_type):
    packet_type = int(rcvd_packet_type,2)
	
    payload = payload.decode('utf-8')

	#Checksum calculation
    check_sum = 0
    for i in range(0, len(payload), 2):
        if (i+1) < len(payload):
            temp_sum = ord(payload[i]) + (ord(payload[i+1]) << 8)
            temp_sum = temp_sum + check_sum
            check_sum = (temp_sum & 0xffff) + (temp_sum >> 16)		
    check_sum_value = check_sum & 0xffff
	
    header = struct.pack('!IHH', int(pkt_no), int(check_sum_value), int(packet_type))
	
    payload = payload.encode('utf-8')
    return header + payload


####################### Client send Function #######################		
def rdt_send(N, server_name, sever_port):
    global current_pkts
    global retransmissions
	
    global timestamp	
    global client_socket

    last_pkt_sent = -1	
    timestamp = [0.0]*total_packets

    while not transfer_end:
        lock.acquire()
        active_packets = len(current_pkts)

        if (active_packets < N) and ((sequence_number + active_packets) < total_packets):
            while not retransmission_queue.empty():
                i = retransmission_queue.get()
                if track_pkts_ack[i] == False:
                    client_socket.sendto(transfer_data[i], (server_name, server_port))				
                    timestamp[i] = current_time()
                    current_pkts.append(i)

            j = last_pkt_sent + 1
            next_pkts = min(sequence_number + N, total_packets)
            while j < next_pkts:
                if track_pkts_ack[j] == False:
                    client_socket.sendto(transfer_data[j], (server_name, server_port))
                    timestamp[j] = current_time()
                    current_pkts.append(j)
                    last_pkt_sent = j
                j = j+1

        active_packets = len(current_pkts)
        done_pkts = []  
        if active_packets > 0:
            for packet_number in current_pkts:
                if track_pkts_ack[packet_number] == True:  
                    done_pkts.append(packet_number)

                elif (current_time() - timestamp[packet_number]) > RTO:
                    if track_pkts_ack[packet_number] == False:
                        if random.random() > 0.6: 
                            print("Time out, Sequence number: " + str(packet_number))
                        retransmission_queue.put(packet_number)
                        retransmissions += 1
                        done_pkts.append(packet_number)


        if len(done_pkts) > 0:
            current_pkts = list(set(current_pkts) - set(done_pkts))
            done_pkts.clear()

        lock.release()

		

####################### Server response Function #######################			
def server_response(client_socket):
    global current_pkts
    global sequence_number
    global transfer_end
    global active_packets

    while not transfer_end:
        active_packets = len(current_pkts)
        if active_packets > 0:
            data = client_socket.recv(2048)  
            lock.acquire()
            ack_number, zero_value, packet_type = packet_deform(data)

            if ack_number in current_pkts:
                current_pkts.remove(ack_number)

            if packet_type == int(final_packet, 2):
                active_packets = 0
                print("Received last ack")
                transfer_end = True
                lock.release()
                break

            assert zero_value == 0, "Invalid Ack from server due to error in zeroes value"
            assert packet_type == int(ack_packet, 2), "Invalid Ack from server due to error in packet type value"				

            if track_pkts_ack[ack_number] == False:  
                track_pkts_ack[ack_number] = True  
                i = sequence_number
                end = min(i+n, total_packets)  
                while i < end and track_pkts_ack[i]:
                    i += 1
                    continue
                sequence_number = i
            lock.release()


####################### Function for deforming the received server packet #######################				
def packet_deform(packet):
    header = struct.unpack('!IHH', packet) 
    ack_number = header[0]
    zeroes = header[1]
    packet_type = header[2]
    return ack_number, zeroes, packet_type
	

	
####################### Run Function #######################
def run():
    global client_socket
    file_read(file_name, mss)
    print("Total number of Packets generated from file : "+str(total_packets))

    client_socket.sendto(str(total_packets).encode(),(server_name,server_port))
	
    t = threading.Thread(target= server_response, args= (client_socket,))
    t.start()
    start_time = current_time()
    rdt_send(n, server_name, server_port)
    t.join()
    end_time = current_time()
    global time_taken
    time_taken = end_time - start_time


	
####################### Main Function #######################			
if __name__ == "__main__":	
    assert len(sys.argv) == 6, "Invalid number of arguments" 

    server_name = str(sys.argv[1])
    server_port = int(int(sys.argv[2]))
    mss = int(sys.argv[3])
    n = int(sys.argv[4])
    file_name = sys.argv[5]	
	
	#Defining lock 
    lock = threading.Lock()
	
	#Server response variables
    ack_received = -1
	
	#Client variables
    total_packets = 0
    track_pkts_ack = []
    transfer_data = []
    sequence_number = 0
    current_pkts = []
    retransmissions = 0
    retransmission_queue = Queue(maxsize=n)
	
    timestamp = []
    
	#Packet type variables
    data_packet = "0101010101010101"  
    final_packet = "1111111111111111"  
    ack_packet = "1010101010101010"  
    
    #Re-transmission timeout
    RTO = 1000 
	
	#Operation time variable
    time_taken = 0
    transfer_end = False
	
	
    #Client address
    client_host = socket.gethostname()
    client_ip = socket.gethostbyname(client_host)
    client_port = 1234
    bind_ip = "0.0.0.0"	
	
    print("Client address: (", client_ip, ",", client_port, ")")
	
	#Server address
    print("Server address: (", server_name, ",", server_port, ")")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((bind_ip, client_port))  
	
	
	#Run operation
    run()

	
	#Printing output stats
    print("Total time for file transfer", time_taken/1000, "s")
    print("Number of Retransmissions", str(retransmissions))
    client_socket.close()