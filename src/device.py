from PIL   			            import Image
import time
import threading
import os
import importlib
import asyncio
import logging

### Omnia libraries ###
from src.omniaClass             import OmniaClass

'''# used for tests
#from src.iot_funct.sound import Sound
#from src.iot_funct.screen import Screen
#from src.iot_funct.display import Display'''
### --- ###

class Device(threading.Thread):

    DEFAULT_WAIT_TIME = 0.1
    WAIT_TIME_IOT = 0.001
    MIN_BLE_RSSI = -70

    def __init__(self, socket, address, device_data, omniaController=None):

        ### Socket ###
        self.socket = socket
        self.socket.setblocking(False)  # async send and receive
        self.address = address    # (IPAddress, Port)
        ### --- ###

        ### Thread ###
        threading.Thread.__init__(self)
        self.name = device_data["name"]     # rename thread with the name of the device 
        self.type = device_data["class"]   # device type
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)  # disable PIL library logging
        self.log = logging.getLogger(
            self.name+'_{}_{}'.format(*self.address)
        )
        ### --- ###

        ### Omnia Protocol and Class ###
        self.loop = asyncio.new_event_loop()    # asyncio loop object
        self.omniaClass = OmniaClass(self.log, device_data)   # new instance of OmniaClass for this user
        self.reader = None      # asyncio StreamReader object
        self.writer = None      # asyncio StreamWriter object
        ### --- ###

        ### Omnia Controller ###
        self.omniaController = omniaController
        ### --- ###

        ### Device data ###
        '''
        device_data structure
        {
            "name": "device_name",
            "class": "device_type"
        }
        '''        
        self.device_data = device_data
        ### --- ###

        ### Proximity detection ###
        self.is_near = False    # True when a user is detected
        self.connect_later = []     # list users that can connect later
        self.last_near_user = None
        ### --- ###

        ### Streaming ###
        self.stream = False     # True if the device is being used
        self.streaming_user = ""    # id of the user that is using this device
        ### --- ###

        ### IOT functions ###
        self.iot_function = None    # class from src/iot_funct that performs a function
        ### --- ###
    
    
    
    ''' Send and Receive '''

    async def recv(self):   # receiving task
        while True:
            self.log.debug("receiving data")
            data = await self.reader.readline()
            self.omniaClass.receivedData(data)
    
    async def __drain(self):
        await self.writer.drain()
    
    def send(self, message):
        self.writer.write(message)
        #await self.writer.drain() # should be called

    ''' --- '''

    # get initial configuration of pins and settings
    async def initConfig(self):
        self.omniaClass.getPinConfig("src/iot/" + self.name + "/pinout.json")
        self.omniaClass.getConfig("src/iot/" + self.name + "/config.json")

        latency_future = self.loop.create_future()
        self.omniaClass.calculateLatency(iterations=30, future=latency_future)

        await latency_future    # await the result of latency calculation

    # set the function the device have to run
    def runIOTFunction(self, iot_function):
        self.log.debug("running iot function {!r}".format(iot_function))
        #self.omniaClass.stopRecvNFC()
        self.omniaClass.stopRecvBLE()   # stop scanning for BLE proximity
        iot_function.start()    # execute the start function from iot_function class
        self.iot_function = iot_function    # set the new iot_function to run
    
    # keep running selected iot_function
    async def __runIOT(self):
        while True:
            if self.iot_function:
                self.iot_function.run()     # run iot_function and return

                wait_time = self.WAIT_TIME_IOT  # wait time for iot function (default)
                
                # check if iot_function has a timing that needs to be respected
                if hasattr(self.iot_function, "time_sleep"):
                    if self.iot_function.time_sleep > 0:
                        wait_time = self.iot_function.time_sleep
                
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(self.DEFAULT_WAIT_TIME)

    def NFCCallback(self, nfc):
        '''nfc = <nfc_id>:'''
        nfc = nfc.split(":")
        '''nfc = ["<nfc_id>", ""]'''
        if(len(nfc) >= 2):  # check if received nfc is valid
            nfc = nfc[1]
            if(not len(nfc) == 8):  # received nfc id is not valid
                nfc = '0'
            else:   # a user is near!
                self.last_near_user = nfc
                self.is_near = True
                self.log.debug("proximity {!r}".format(nfc))
    
    def BLECallback(self, ble):
        ''' ble = <rssi>+<first_id>,<rssi>+<second_id>,...'''
        ble = ble.split(',')

        nearest_RSSI = -200     # out of range initial value
        nearest_user = ""

        if len(ble) >= 1:   # if at least one user is near
            for user in ble:
                user = user.split("+")  # split id and rssi
                if len(user) >= 2:  # if it's valid
                    rssi = int(user[0])
                    user_id = user[1]
                    if self.omniaController.isValidUser(user_id):   # if this user is registered in Omnia
                        self.log.debug("detected user with id: '{!r}'".format(user_id))
                        if rssi >= self.MIN_BLE_RSSI:   # if user is near
                            self.log.debug("near user: '{!r}'".format(rssi))
                            if rssi > nearest_RSSI:     # if the user is the nearest
                                nearest_RSSI = rssi
                                nearest_user = user_id
                                self.log.debug("NEAREST USER: '{!r}'".format(nearest_user))
            
            if nearest_user != "":
                self.last_near_user = nearest_user
                self.is_near = True
                self.log.debug("DETECTED PROXIMITY: user_id='{!r}'".format(nearest_user))
                #self.omniaClass.stopRecvBLE()
    
    def getLastNearUser(self):
        return self.last_near_user

    # enable user to stream later
    def streamLater(self, username):    
        if not username in self.connect_later:
            self.connect_later.append(username)
    
    # True if the user can stream later
    def canStreamLater(self, username):
        if username in self.connect_later:
            return True

        return False
    
    # stop running iot_function and reset streaming parameters
    def resetStreamingUser(self):
        self.log.debug("resetting streaming user")

        self.streamLater(self.streaming_user)   # remember user to stream later

        self.streaming_user = ""
        self.stream = False
        # self.is_near = False
        # self.omniaClass.startRecvNFC(self.NFCCallback)
        self.omniaClass.startRecvBLE(self.BLECallback)  # listen to BLE again
        self.iot_function = None    # reset iot_function
    
    # set who is using the device
    def setStreamingUser(self, user):
        self.streaming_user = user
        self.stream = True

    def getStreamingUser(self):
        return self.streaming_user

    def getDeviceName(self):
        return self.name

    def getDeviceType(self):
        return self.type

    def run(self):
        
        # generate asyncio socket interfaces: 
        #   reader <-> receive
        #   writer <-> send 
        self.reader, self.writer = self.loop.run_until_complete(asyncio.open_connection(sock=self.socket))
        self.omniaClass.setSendFunction(self.send)  # set omniaClass send function

        # create receive task
        recv_task = self.loop.create_task(self.recv())        

        '''# used for tests

        # s = Sound("eulero", None)
        # s.handleStreaming(self)
        # self.runIOTFunction(s)

        # f = Screen("eulero", None)
        # f.handleStreaming(self)
        # self.runIOTFunction(f)

        # f = Display("eulero", None)
        # f.handleStreaming(self)
        # self.runIOTFunction(f)

        # self.omniaController.addUser({"name": "eulero", "uid":"eulero"})
        # self.omniaController.omnia_media_sharing.setAttribute("eulero", "pause", True)

        # f = self.omniaController.getIOTFunction("eulero", self.type)
        # f.handleStreaming(self)
        # self.runIOTFunction(f)'''

        # create task that runs the iot_function
        iot_task = self.loop.create_task(self.__runIOT())

        # wait this task so we can get the latency
        self.loop.run_until_complete(self.initConfig())

        # self.omniaClass.startRecvNFC(self.NFCCallback)
        self.omniaClass.startRecvBLE(self.BLECallback)

        try:
            self.loop.run_forever()     # run tasks continuously
        except KeyboardInterrupt:   # stop if Ctrl-C
            self.log.debug("closing {!r} socket".format(self.name))
            pass

        self.loop.close()   # stop tasks and close loop

    def resumeConnection(self, socket):
        self.socket = socket
        self.omniaClass.getPinConfig("src/iot/" + self.name + "/pinout.json")
        # self.omniaClass.resumeImg()
        self.log.debug("resumed")
