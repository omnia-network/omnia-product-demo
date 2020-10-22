import socket
import json
import logging
import sys
import threading

### Omnia libraries ###
from src.device 			import Device
from src.omniaController 	import OmniaController
from src.user				import User
### --- ###

logging.basicConfig(
            level=logging.DEBUG,
            format='%(name)s: %(message)s',
            stream=sys.stderr,
        )

log = logging.getLogger('main')

'''
threads structure
{
    "username":{    # user_name or device_name
       "thread": user/device's thread instance,
       "instance": User/Device class instance
    }
}
'''
threads = {}   # list of users and devices objects

users_path = "users.json"
devices_path = "devices.json"

'''
USERS structure
{
    "mac-address":{     # mac address of the user's watch
        "name": "user_name",
        "uid": "user id"    # RFID or BLE 
    }
}
'''
users = {}      # list of users

'''
DEVICES structure
{
    "mac-address":{     # mac address of the device
        "name": "device name",
        "class": "type of device"    # one of the applications in src/iot_funct folder
    }
}
'''
devices = {}    # list of devices

# create file objects used to reference files containing users and devices
with open(users_path, "r") as rf:
    users = json.load(rf)

with open(devices_path, "r") as rf:
    devices = json.load(rf)

# server IP address and port
#ADDRESS = socket.gethostbyname( socket.gethostname() )    # IP of this machine
ADDRESS = "192.168.1.10"
PORT = 50500                                # randomly chosen

# create TCP/IP socket for new connections
new_conn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
new_conn_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
new_conn_sock.bind((ADDRESS, PORT))

new_conn_sock.listen()   # listen for new clients

# init instance of OmniaController class, shared by all users and devices
omniaController = OmniaController()

log.info("SERVER STARTED")      # here we go :)

while(1):

    # create a new socket for every client that connects to the server
    client_socket, client_address = new_conn_sock.accept()
    #client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)	# send data separately

    # got new connection
    log.debug("-----")
    log.debug("NEW CONNECTION")
    log.debug(client_address)

    # receive client's mac address
    client_mac = client_socket.recv(12).decode()
    
    log.debug(client_mac)

    # print(client_socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
    # SEND_BUF_SIZE = 4096
    # client_socket.setsockopt(
    #     socket.SOL_SOCKET,
    #     socket.SO_SNDBUF,
    #     SEND_BUF_SIZE)

    # create a thread for every user connected
    if client_mac in users:     # client is a user
        user_data = users[client_mac]    # get user data at this mac
        user_name = user_data["name"]

        if user_name in threads and threads[user_name]["thread"].is_alive():     # thread already running for this user
            log.debug("resuming USER: {!r}".format(user_name))
            #threads[user_name]["thread"].resumeConnection(client_socket)   # resume connection with new socket
  
        else:
            # if user_name in threads:    # user had already connected but thread died
            #     log.debug("dead USER {!r}".format(user_name))
            #     threads.pop(user_name)
            #     omniaController.removeUser(user_name)

            log.debug("connecting USER: {!r}".format(user_name))
            
            # create a User class instance for this user
            user = User(client_socket, client_address, user_data, omniaController)
            omniaController.addUser(user_data)

            # create thread for the new user
            th = threading.Thread(target=user.main, name=user_name, daemon=True)
            threads.__setitem__(user_name, {"thread": th, "instance": user})   # add user's thread and instance to threads
            th.start()    #start user's thread

    elif client_mac in devices: # client is a device
        device_data = devices[client_mac]    # get device data at this mac
        device_name = device_data["name"]
        
        if device_name in threads and threads[device_name]["thread"].is_alive():   # thread already running for this device
            log.debug("resuming DEVICE: {!r}".format(device_name))
            #threads[device_name]["thread"].resumeConnection(client_socket)    # resume connection with new socket
            
        else:
            # if device_name in threads:
            #     log.debug("dead DEVICE {!r}".format(device_name))
            #     threads.pop(device_name)
            #     omniaController.removeDevice(device_name)
        
            log.debug("connecting DEVICE: {!r}".format(device_name))

            # create a Device class instance for this device
            device = Device(client_socket, client_address, device_data, omniaController)
            omniaController.addDevice(device)

            # create thread for the new device
            th = threading.Thread(target=device.main, name=device_name, daemon=True)
            threads.__setitem__(device_name, {"thread": th, "instance": device})   # add device's thread and instance to threads
            th.start()    # start device's thread

    log.debug("Clients connected: {!r}".format(len(threads)))
    log.debug("-----")
