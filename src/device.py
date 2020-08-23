from src.omniaClass             import OmniaClass

from PIL   			            import Image
import time
import threading
import os
import importlib
import asyncio
import logging

class Device(threading.Thread):

    def __init__(self, socket, address, deviceData, omnia_controller=None):

        ### Socket ###
        self.sc=socket
        self.sc.setblocking(False)
        self.address=address
        ### --- ###

        ### Thread ###
        threading.Thread.__init__(self)
        self.name=deviceData["name"]
        self.type=deviceData["class"]
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)
        self.log = logging.getLogger(
            self.name+'_{}_{}'.format(*self.address)
        )
        ### --- ###

        ### Omnia Protocol and Class ###
        self.loop = asyncio.new_event_loop()

        self.omniacls = OmniaClass(self.log, deviceData)
        self.reader = None
        self.writer = None
        ### --- ###

        ### Device Data ###
        self.deviceData = deviceData
        ### --- ###

        ### Application ###
        self.app = None
        ### --- ###

        ### Streaming ###
        self.isNear = False
        self.stream = False
        self.streamingUser = ""
        ### --- ###

        ### IOT functions ###
        self.iot_function = None
        ### --- ###        

        ### I/O data ###
        self.data = 0
        self.buttons = {}
        ### --- ###

        ### Flags ###
        self.alive = True
        self.canSend = True
        ### --- ###

        ### NFC ###
        self.nfc = None
        ### --- ###

        ### Handle send ###
        self.sendType = None
        ### --- ###
    
    ''' Send and Receive '''

    async def recv(self):
        while True:
            self.log.debug("receiving data")
            data = await self.reader.readline()
            self.omniacls.receivedData(data)
    
    async def __drain(self):
        await self.writer.drain()
    
    def send(self, message):
        self.writer.write(message)
        self.loop.create_task(self.__drain())

    ''' --- '''

    def init_config(self):
        self.omniacls.getPinConfig("src/iot/"+self.name+"/pinout.json")
        self.omniacls.getConfig("src/iot/"+self.name+"/config.json")

    def runIOTFunction(self, iot_function):
        self.log.debug("running iot function {!r}".format(iot_function))
        self.omniacls.stopRecvNFC()
        iot_function.start()
        self.iot_function = iot_function
    
    async def __run_iot(self):
        while True:
            if self.iot_function:
                self.iot_function.run()

            await asyncio.sleep(0.1)

    def NFCCallback(self, nfc):

        nfc=nfc.split(":")
        if(len(nfc)>=2):
            nfc=nfc[1]
            if(not len(nfc)==8):
                nfc='0'
            else:
                self.nfc = nfc
                self.isNear = True
                self.log.debug("proximity {!r}".format(nfc))
    
    def getNFC(self):
        return self.nfc
    
    def resetStreamingUser(self):
        self.log.debug("resetting streaming user")
        self.streamingUser=""
        self.stream = False
        self.isNear = False
        self.omniacls.startRecvNFC(self.NFCCallback)
        self.iot_function = None
    
    def setStreamingUser(self, user):
        self.streamingUser=user
        self.stream = True

    def getStreamingUser(self):
        return self.streamingUser

    def getDeviceName(self):
        return self.name

    def getDeviceType(self):
        return self.type

    def run(self):

        self.reader, self.writer = self.loop.run_until_complete(asyncio.open_connection(sock=self.sc))

        self.omniacls.setSendFunction(self.send)
        
        self.init_config()

        recv_task = self.loop.create_task(self.recv())

        iot_task = self.loop.create_task(self.__run_iot())

        self.omniacls.startRecvNFC(self.NFCCallback)

        try:
            # Run the event loop
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.log.debug("closing {!r} socket".format(self.name))
            pass

        self.loop.close()

    def resumeConnection(self, so):
        self.sc = so
        self.omniacls.getPinConfig("src/iot/"+self.name+"/pinout.json")
        #self.omniacls.resumeImg()
        self.log.debug("resumed")
