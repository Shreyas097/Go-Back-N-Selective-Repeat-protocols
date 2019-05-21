Submitted by:
Name 1: Shreyas Srinivasan 
Student ID: 200255421
Name 2: Santhosh Ravisankar 
Student ID: 200261510

Environment:
Python 3

Execution:
For execution do the following:
Run the server first on a machine of choice using the following command

python server.py <server_port_number> <file_name> <packet_loss_prob>

Example:

python server.py 7735 download.txt 0.05

Then run the client in any other sytem or the same machine

python client.py <server_host_name> <server_port> <file_name_to_be_uploaded> <window_size>

If using the same machine, give the server ip as localhost

python client.py localhost <server_port> <Maximum_segment_size> <window_size> <file_name_to_be_transferred>

Example:

python client.py 192.168.1.32 7735 500 64 test1Mb.db

For running client and server on the same machine

python client.py localhost 7735 500 64 test1Mb.db