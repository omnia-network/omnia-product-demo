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

users_path="users.json"
devices_path="devices.json"

users = {}
devices = {}

with open(users_path, "r") as rf:
    users = json.load(rf)

with open(devices_path, "r") as rf:
    devices = json.load(rf)

adress="192.168.1.4"
serv_port=50500
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((adress, serv_port))
sock.listen()

omnia_controller = OmniaController()

log.info("SERVER STARTED")

while(1):

    so, adr=sock.accept()
    #so.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)	# send data separately
    log.debug("-----")
    log.debug("NEW CONNECTION")
    log.debug(adr)
    mac=so.recv(12)
    mac = mac.decode()
    log.debug(mac)

    # print(so.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
    # SEND_BUF_SIZE = 4096
    # so.setsockopt(
    #     socket.SOL_SOCKET,
    #     socket.SO_SNDBUF,
    #     SEND_BUF_SIZE)
        
    username = ''
    device = ''

    if mac in users:
        userData = users[mac]
        username = userData["name"]


        if username in threadAssign and threadAssign[username]["thread"].isAlive():
            log.debug("resuming USER: {!r}".format(username))
            #threadAssign[username]["thread"].resumeConnection(so)
            
        else:
            if username in threadAssign:
                log.debug("dead USER {!r}".format(username))
                threadAssign.pop(username)
                omnia_controller.removeUser(username)

            log.debug("connecting USER: {!r}".format(username))
            
            user=User(so, adr, userData, omnia_controller)
            omnia_controller.addUser(userData)

            threadAssign.__setitem__(username, {"thread": user})
            user.start()

    elif mac in devices:
        deviceData = devices[mac]
        deviceName = deviceData["name"]
        

        if deviceName in threadAssign and threadAssign[deviceName]["thread"].isAlive():
            log.debug("resuming DEVICE: {!r}".format(deviceName))
            threadAssign[deviceName]["thread"].resumeConnection(so)
            
        else:
            if deviceName in threadAssign:
                log.debug("dead DEVICE {!r}".format(deviceName))
                threadAssign.pop(deviceName)
                omnia_controller.removeDevice(deviceName)
        
            log.debug("connecting DEVICE: {!r}".format(deviceName))

            dev = Device(so, adr, deviceData, omnia_controller)
            dev.start()
            threadAssign.__setitem__(deviceName, {"thread": dev})
            omnia_controller.addDevice(dev)

    log.debug("Clients connected: {!r}".format(len(threadAssign)))
    log.debug("-----")
