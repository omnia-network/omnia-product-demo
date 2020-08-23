'''from eulero.src.menu  		import Menu
from eulero.src.clock 		import Clock
from eulero.src.torch 		import Torch
from eulero.src.weather	    import Weather
from eulero.src.settings 	import Settings
from eulero.src.stream      import Stream
from eulero.src.profile     import ProfilePic'''

from src.notifyService          import NotifyService
from src.omniaClass             import OmniaClass

from PIL   			            import Image
import time
import threading
import os
import importlib
import asyncio
import logging

class User(threading.Thread):

    def __init__(self, socket, address, userData, omnia_controller=None):

        ### Socket ###
        self.sc=socket
        self.sc.setblocking(False)
        self.address=address
        ### --- ###

        ### Thread ###
        threading.Thread.__init__(self)
        self.name = userData["name"]
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)
        self.log = logging.getLogger(
            self.name+'_{}_{}'.format(*self.address)
        )
        ### --- ###

        ### Omnia Protocol and Class ###
        self.loop = asyncio.new_event_loop()

        self.omniacls = OmniaClass(self.log, userData, self.protocol)
        self.reader = None
        self.writer = None
        ### --- ###

        ### Omnia Controller ###
        self.omnia_controller = omnia_controller
        ### --- ###

        ### User Data ###
        self.userData = userData
        ### --- ###

        ### Applications ###
        self.applications = []       #list of apps objects
        self.applications_name = []  #list of apps names
        ### --- ###       

        ### I/O data ###
        self.data=0
        self.buttons={}
        ### --- ###

        ### Flags ###
        self.alive=True
        self.canSend=True
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
        self.omniacls.getPinConfig(self.name+"/src/config/pinout.json")
        self.omniacls.getConfig(self.name+"/src/config/config.json")

    async def init_connection(self):

        pic=Image.open(self.name+"/src/images/pic.png")
        self.omniacls.setImg(pic)
        self.omniacls.sendImg()
        await asyncio.sleep(3)

        self.omniacls.newImg()
        self.omniacls.setText((10,0),"GBROS", 255,self.omniacls.getFonts()[1])
        self.omniacls.setText((18,32),"V "+self.omniacls.getVersion(), 255,self.omniacls.getFonts()[1])
        self.omniacls.sendImg()
        #await asyncio.sleep(3)

        userAppsPath = self.name+"/src/"

        apps = []
        if os.path.exists(userAppsPath):
            for (_, _, filenames) in os.walk(userAppsPath):
                apps.extend(filenames)
                break
    
        apps.sort()

        self.prepareApps(apps)
    
    def prepareApps(self, apps):
        for app in apps:
            appName = app[:-3]      # remove .py extension
            if appName[0] != "_":   # do not import apps that start with "_"
                self.log.debug("loading app: {!r}".format(appName.upper()))
                appObj = getattr(importlib.import_module(self.name+".src."+appName), appName.capitalize())
                self.applications.append(appObj(self.omniacls))
                self.applications_name.append(appName.upper())
            else:
                self.log.debug("ignoring app: {!r}".format(appName[1:].upper()))

    async def runApps(self):
        await asyncio.sleep(6)
        self.log.debug("loading MENU")
        Menu = getattr(importlib.import_module(self.name+".menu"), "Menu")
        menu=Menu(self.omniacls, self.applications_name)
        
        i = 0
        self.log.debug("starting app: {!r}".format(self.applications_name[i]))

        while(self.omniacls.isAlive()):
            if(i==-1):
                self.log.debug("starting menu")

                i = await menu.run()

                self.log.debug("exited menu")
                self.log.debug("starting app: {!r}".format(self.applications_name[i]))
            else:
                running_app = self.applications_name[i]

                i = await self.applications[i].run()

                self.log.debug("exited {!r}".format(running_app))
                if i != -1:
                    self.log.debug("starting app: {!r}".format(self.applications_name[i]))

    def run(self):

        self.reader, self.writer = self.loop.run_until_complete(asyncio.open_connection(sock=self.sc))

        self.omniacls.setSendFunction(self.send)
        
        self.init_config()

        #init_task = self.loop.create_task(self.init_config())

        recv_task = self.loop.create_task(self.recv())

        #asyncio.run(self.init_config())
        self.loop.create_task(self.init_connection())
        #self.loop.run_until_complete(self.init_config())

        #self.loop.run_until_complete(self.init_connection())

        apps_task = self.loop.create_task(self.runApps())

        notification = NotifyService(self.omniacls, self.omnia_controller, self.log)
        notification_task = self.loop.create_task(notification.run())

        try:
            # Run the event loop
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.log.debug("closing {!r} socket".format(self.name))
            pass

        self.loop.close()

    def resumeConnection(self, so):
        self.sc = so
        self.omniacls.getPinConfig(self.name+"/src/config/pinout.json")
        self.omniacls.resumeImg()
        self.log.debug("resumed")
