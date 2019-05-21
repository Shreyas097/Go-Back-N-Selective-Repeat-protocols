import socket
import sys
import threading
import time
import struct

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
        total_packets = len(transfer_data)
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
def rdt_send(N, server_name, server_port):
    global client_socket
    global timestamp
    global sequence_number
    global current_pkt_number


    sequence_number = ack_received + 1 
    timestamp = [0.0]*total_packets
	

    while sequence_number < total_packets:
        lock.acquire()
        if (current_pkt_number < N):											
            packet_transfer = None
            if ((sequence_number + current_pkt_number) < total_packets):		
                packet_transfer = transfer_data[sequence_number + current_pkt_number]
                assert packet_transfer != None, "No message to transfer"
                client_socket.sendto(packet_transfer,(server_name, server_port))
                timestamp[sequence_number + current_pkt_number] = current_time()
                current_pkt_number = current_pkt_number + 1
        if (current_pkt_number > 0) and ((current_time() - timestamp[sequence_number]) > RTO):
            global retransmissions
            retransmissions = retransmissions + 1
            print("Time out, Sequence number: " + str(sequence_number))
            current_pkt_number = 0
        lock.release()


		
####################### Server response Function #######################		
def server_response(client_socket):
    global current_pkt_number 
    global ack_received
    global sequence_number
    
	
    while sequence_number < total_packets:
        if (current_pkt_number > 0):
            data = client_socket.recv(2048)
            assert data != None, "Server Connection timed out - Empty response from server"
			
            lock.acquire()
            ack_number, zero_value, packet_type = packet_deform(data)
			
            assert zero_value == 0, "Invalid Ack from server due to error in zeroes value"
            assert bin(packet_type) == ack_packet, "Invalid Ack from server due to error in packet type value"
						
            if (ack_number == sequence_number):
                current_pkt_number = current_pkt_number - 1
                ack_received = sequence_number
                sequence_number = sequence_number + 1
            else:
                current_pkt_number = 0
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
    file_read(file_name, MSS)
    print("Total number of Packets generated from file : "+str(total_packets))
	
    t = threading.Thread(target= server_response, args= (client_socket,))
    t.start()
    start_time = current_time()
    rdt_send(N, server_name, server_port)
    t.join()
    end_time = current_time()
    global time_taken
    time_taken = end_time - start_time


	
####################### Main Function #######################			
if __name__ == "__main__":	
    assert len(sys.argv) == 6, "Invalid number of arguments" 

    server_name = str(sys.argv[1])
    server_port = int(int(sys.argv[2]))
    MSS = int(sys.argv[3])
    N = int(sys.argv[4])
    file_name = sys.argv[5]	
	
	#Defining lock 
    lock = threading.Lock()
	
	#Server response variables
    ack_received = -1
	
	#Client variables
    total_packets = 0
    transfer_data = []
    sequence_number = 0
    current_pkt_number = 0
    retransmissions = 0
	
    timestamp = []
    
	#Packet type variables
    data_packet = "0101010101010101"  
    final_packet = "1111111111111111"  
    ack_packet = "0b1010101010101010"  
    
    #Re-transmission timeout
    RTO = 100 
	
	#Operation time variable
    time_taken = 0
	
	
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
