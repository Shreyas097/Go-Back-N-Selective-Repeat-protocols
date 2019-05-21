import socket
import random
import struct
import time
import sys

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
def pkt_ack(server_socket, client_address, sequence_number, zeros, packet_type):
    tcp_header = struct.pack("!IHH", sequence_number, int(zeros, 2), int(packet_type, 2))
    server_socket.sendto(tcp_header, client_address)


	
####################### Main Function #######################	
if __name__ == '__main__':
    assert len(sys.argv) == 4, "Invalid number of arguments" 

    SERVER_PORT = int(sys.argv[1])
    locFILE = sys.argv[2]
    lossprob = float(sys.argv[3])
	
	#Client address
    CLIENT_PORT = 1234
    HOST_NAME = '0.0.0.0'

	#Server address
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', SERVER_PORT))
    print("Server started and is listening at port : ", SERVER_PORT)	

	#Packet type variables	
    b16_pkt_type_data = "0101010101010101"
    b16_pkt_type_ack = "1010101010101010"
    zeros = "0000000000000000"
    b16_fin = '1111111111111111'
	
	#Server variables
    rcvd_pkts = {}
    flag = True

    write_file = open(locFILE, "w")

    data, addr = server_socket.recvfrom(2048)
    total_packets = int(data.decode())
    print("Total number of packets: ", total_packets)

    start_time = current_time()
    end_time = 0

    while flag:
        data, addr = server_socket.recvfrom(2048)
        client_host_name = addr[0]
        seq_num, checksum, pkt_type, data = packet_deform(data)

        if calculate_checksum(data,checksum) != 0 :
            print('Faulty Checksum, sequence number = ', str(seq_num))		# Check check sum will return 0 only if there is not issues in the checksum of the computed
        
        else:
            if random.random() < lossprob:									# the packet has to be dropped
                print('Packet loss, sequence number = ', str(seq_num))
                continue

            if pkt_type == int(b16_fin, 2):									
                pkt_ack(server_socket, (client_host_name, CLIENT_PORT), seq_num, zeros, b16_pkt_type_ack)
                continue

            assert pkt_type == int(b16_pkt_type_data, 2), "Invalid message from client due to error in packet type value"
				
            if not int(seq_num) in rcvd_pkts:
                rcvd_pkts[int(seq_num)] = data
                total_packets -= 1
                if total_packets <= 1:
                    flag = False
                    end_time = current_time()
                    pkt_ack(server_socket, (client_host_name, CLIENT_PORT), seq_num, zeros, b16_fin)
                    print("Sent last ack")
                    break

            pkt_ack(server_socket, (client_host_name, CLIENT_PORT), seq_num, zeros, b16_pkt_type_ack)
	

    print("Total time for file reception:", (end_time - start_time)/1000)

    for i in range(total_packets):
        if i in rcvd_pkts:
            write_file.write(rcvd_pkts[i])	
    write_file.close()
    server_socket.close()
    sys.exit()
