import socket
import sys
import random
import struct
import time


####################### Function for noting current time #######################	
def current_time():
	return int(round(time.time() * 1000 ))
	

####################### Function for deforming the received server packet #######################		
def packet_deform(packet):
    tcp_header = struct.unpack('!IHH', packet[0:8]) 
    seq_num = tcp_header[0]
    check_sum = tcp_header[1]
    pkt_type = tcp_header[2]
    data = packet[8:] 
    data = data.decode('utf-8')
    return seq_num, check_sum, pkt_type , data


####################### Function for calculating checksum #######################	
def calculate_checksum(packet, chksum_client):
    sum = 0
    check_sum = 0
    for i in range(0, len(packet), 2):
        if (i + 1) < len(packet):
            temp_sum = ord(packet[i]) + (ord(packet[i + 1]) << 8)
            temp_sum = temp_sum + sum
            sum = (temp_sum & 0xffff) + (temp_sum >> 16)
    check_sum = (~sum & 0xffff) & chksum_client
    return check_sum

	
####################### Function for sending acknowledgements #######################		
def pkt_ack(server_socket, client_address, seq_num,zeros,pkt_type):
    tcp_header = struct.pack("!IHH",seq_num,int(zeros, 2),int(pkt_type, 2))
    server_socket.sendto(tcp_header,client_address)


	
####################### Function for initialization #######################		
def initialize():
    assert len(sys.argv) == 4, "Invalid number of arguments" 

    global SERVER_PORT
    global locFILE
    global lossprob
	
    SERVER_PORT = int(sys.argv[1])
    locFILE = sys.argv[2]
    lossprob = float(sys.argv[3])	
	
	#Packet type variables	
    global b16_pkt_type_data
    global b16_pkt_type_ack 
    global b16_fin
    global zeros
    b16_pkt_type_data = "0101010101010101"
    b16_pkt_type_ack = "1010101010101010"
    zeros = "0000000000000000"
    b16_fin = '1111111111111111'

	#Client address	
    global CLIENT_PORT
    global HOST_NAME
    CLIENT_PORT = 1234
    HOST_NAME = '0.0.0.0'

	#Server variables	
    global prev_val	
    prev_val = -1
	
    global write_file
    write_file = open(locFILE,"w")	

	#Server address	
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST_NAME,SERVER_PORT))
    print("Server started and is listening at port : ",SERVER_PORT)


	
####################### Main Function #######################	
if __name__ == '__main__':
  
    initialize()

    start_time = current_time()
    end_time = 0	

    while True:
        data, addr = server_socket.recvfrom(2048)
        client_host_name = addr[0]
        seq_num, checksum, pkt_type, data = packet_deform(data)

        if calculate_checksum(data,checksum) != 0 :
            print('Faulty Checksum, sequence number = ', str(seq_num))				# Check check sum will return 0 only if there is not issues in the checksum of the computed

        else:

            if random.random() < lossprob:											# the packet has to be dropped
                print('Packet loss, sequence number = ', str(seq_num))
                continue

            if seq_num == prev_val + 1:
                if pkt_type == int(b16_fin, 2):										#sending the last acknowledgement
                    pkt_ack(server_socket, (client_host_name, CLIENT_PORT), seq_num, zeros, b16_pkt_type_ack)
                    end_time = current_time()
                    print("Data download complete")
                    break

                assert pkt_type == int(b16_pkt_type_data, 2), "Invalid message from client due to error in packet type value"

                pkt_ack(server_socket, (client_host_name,CLIENT_PORT), seq_num, zeros, b16_pkt_type_ack)
                prev_val += 1
                write_file.write(data)
   
    print("Total time for file reception:", (end_time - start_time)/1000)
    write_file.close()
    server_socket.close()