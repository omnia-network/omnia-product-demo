import socket
from omniaClient import OmniaClient
import uuid

# get mac address
mac = ''.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])

# configuration port for new client
connport = 50500

# server address
host = "192.168.0.2"
#host="lucab.ddns.net"
adress = socket.getaddrinfo(host,connport)[0][-1][0]

# setting which I/O devices are connected to the client
client = OmniaClient('ili9341', touch='xpt2046')
#client = OmniaClient('audio')

so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
so.connect((adress, connport))
so.send(mac.encode())

# print(so.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))
# RECV_BUF_SIZE = 4096
# so.setsockopt(
#     socket.SOL_SOCKET,
#     socket.SO_RCVBUF,
#     RECV_BUF_SIZE)

client.setSocket(so)

# run client firmware
client.run()

print("end")
