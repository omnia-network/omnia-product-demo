from PIL import Image, ImageDraw, ImageFont, ImageOps
import json
import asyncio
import os
import logging
import importlib

from src.omniaMediaSharing      import OmniaMediaSharing

class OmniaController:
    def __init__(self):
        self.devices = []
        self.nearDevices = {}
        self.streamingDevices = []
        self.users = {}

        ### Sharing ###
        self.omnia_media_sharing = OmniaMediaSharing()
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)
        self.log = logging.getLogger('controller')
        ### --- ###

        with open("src/userDevices.json", "r") as rf:
            self.userDevices = json.load(rf)
        
        self.iot_imports = {}

        self.importIOTFunctions()

    def importIOTFunctions(self):
        iot_funct_path ="src/iot_funct"

        iot_functions = []
        if os.path.exists(iot_funct_path):
            for (_, _, filenames) in os.walk(iot_funct_path):
                iot_functions.extend(filenames)
                break
    
        iot_functions.sort()

        for iot in iot_functions:
            appName = iot[:-3]      # remove .py extension
            if appName[0] != "_":   # do not import apps that start with "_"
                self.log.debug("loading IOT function: {!r}".format(appName.upper()))
                appObj = getattr(importlib.import_module("src.iot_funct."+appName), appName.capitalize())
                self.iot_imports[appName] = appObj
            else:
                self.log.debug("ignoring IOT function: {!r}".format(appName[1:].upper()))
    
    def getIOTFunction(self, username, deviceType):
        iot_fn = self.users[username]["iot"][deviceType]

        return iot_fn

    def addDevice(self, device):
        self.devices.append(device)
    
    def removeDevice(self, device):
        if device in self.devices:
            self.devices.remove(device)
    
    def addUser(self, user):
        iot_functions = {}
        for iot in self.iot_imports:
            iot_functions[iot] = self.iot_imports[iot](user["name"], self)
        
        self.users[user["name"]] =  {
            "uid": user["uid"],
            "iot": iot_functions
        }
    
    def removeUser(self, username):
        if username in self.users:
            self.users.pop(username)

    def __addNearDevice(self, device, user):
        if not (user in self.nearDevices):
            self.nearDevices.__setitem__(user, [])
        
        if not (device in self.nearDevices[user]):
            self.nearDevices[user].append(device)
	
    def __removeNearDevice(self, device, user):
        if user in self.nearDevices:
            if device in self.nearDevices[user]:
                device.stream = False
                self.nearDevices[user].remove(device)
	
    def __updateNearDevices(self, user):
        for device in self.devices:
            if device.isNear:
                if device.getLastNearUser() == self.users[user]["uid"]:
                    if device.name in self.userDevices[user]:
                        #device.omniacls.stopRecvNFC()
                        self.__addNearDevice(device, user)
            else:
                self.__removeNearDevice(device, user)

    async def listNearDevices(self, user):
        self.__updateNearDevices(user)
        
        availableDevices = []
        #print(self.nearDevices)
        if user in self.nearDevices:
            for device in self.nearDevices[user]:
                #if device.streamingUser == "" or device.streamingUser == user:
                availableDevices.append(device)
        
        #print(availableDevices)
        return availableDevices
    
    def streamOnDevice(self, dev, user):
        if dev.stream:
            dev.stream = False
            dev.streamingUser = ""
            self.streamingDevices.remove(dev)
            return 0
        else:
            dev.stream = True
            dev.streamingUser = user
            self.streamingDevices.append(dev)

            for device in self.nearDevices:
                if device != dev:
                    if device.streamingUser == user:
                        device.stream=False
                        device.streamingUser = ""
            
            return dev
    
    def isValidUser(self, user):
        if user in self.users:
            return True
        else:
            return False
