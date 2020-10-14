import socket
import importlib
import json
import binascii
import logging
import sys

from src.device 			import Device
from src.omniaController 	import OmniaController
from src.user				import User

logging.basicConfig(
            level=logging.DEBUG,
            format='%(name)s: %(message)s',
            stream=sys.stderr,
        )

log = logging.getLogger('main')

threadAssign = {}

users_path = "users.json"
devices_path = "devices.json"

users = {}
devices = {}

# read all users that joined the network
with open(users_path, "r") as rf:
	users = json.load(rf)

# read all devices that are part of the network
with open(devices_path, "r") as rf:
	devices = json.load(rf)

# server socket initialization for TCP/IP
adress = "172.20.10.2"
serv_port = 50500
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((adress, serv_port))

# start listening on the socket
sock.listen()

# omnia_controller is the class that manages users and devices in the network
omnia_controller = OmniaController()

log.info("SERVER STARTED")

while(1):

	so, adr = sock.accept()		# wait until new connection
	#so.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)	# send data separately
	log.debug("-----")
	log.debug("NEW CONNECTION")
	log.debug(adr)
	mac = so.recv(6)	# receive client MAC address
	mac = binascii.hexlify(mac).decode()
	log.debug(mac)
	
	username = ''
	device = ''

	# check if the new client is a user or a device

	# if the new client is a user
	if mac in users:
		userData = users[mac]
		username = userData["name"]

		# if the user thread is still alive, resume connection
		if username in threadAssign and threadAssign[username]["thread"].isAlive():
			log.debug("resuming USER: {!r}".format(username))
			threadAssign[username]["thread"].resumeConnection(so)
			
		else:

			# if the user thread is dead, terminate thread
			if username in threadAssign:
				log.debug("dead USER {!r}".format(username))
				threadAssign.pop(username)
				omnia_controller.removeUser(username)
			
			# initialize user
			log.debug("connecting USER: {!r}".format(username))
			user = User(so, adr, userData, omnia_controller)
			omnia_controller.addUser(userData)
			# create new thread
			threadAssign.__setitem__(username, {"thread": user})
			user.start()

	# if the new client is a device
	elif mac in devices:
		deviceData = devices[mac]
		deviceName = deviceData["name"]
		
		# if the device thread s still alive, resume connection
		if deviceName in threadAssign and threadAssign[deviceName]["thread"].isAlive():
			log.debug("resuming DEVICE: {!r}".format(deviceName))
			threadAssign[deviceName]["thread"].resumeConnection(so)
			
		else:

			# if the device thread is dead, terminate thread
			if deviceName in threadAssign:
				log.debug("dead DEVICE {!r}".format(deviceName))
				threadAssign.pop(deviceName)
				omnia_controller.removeDevice(deviceName)
		
			# initialize device
			log.debug("connecting DEVICE: {!r}".format(deviceName))
			dev = Device(so, adr, deviceData, omnia_controller)
			omnia_controller.addDevice(dev)
			# create new thread
			threadAssign.__setitem__(deviceName, {"thread": dev})
			dev.start()

	# display number of connected clients
	log.debug("Clients connected: {!r}".format(len(threadAssign)))
	log.debug("-----")
