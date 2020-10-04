import network
import socket
import firmware
import time
import ubinascii

wlan=network.WLAN()

# get esp mac address
mac=wlan.config('mac')
mac=ubinascii.hexlify(mac)

while not wlan.isconnected():
    pass

# configuration port for new client
connport=50500

# server address
host="192.168.1.10"
#host="lucab.ddns.net"
adress = socket.getaddrinfo(host,connport)[0][-1][0]

so=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
so.connect((adress, connport))
so.send(mac.encode())

#time.sleep(1)

# run client firmware with communication port
firmware.run(so)

print("end")