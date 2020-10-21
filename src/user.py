from PIL   			            import Image
import threading
import os
import importlib
import asyncio
import logging

### Omnia libraries ###
from src.notifyService          import NotifyService
from src.omniaClass             import OmniaClass
### --- ###

class User(threading.Thread):

    def __init__(self, socket, address, user_data, omniaController=None):

        ### Socket ###
        self.socket = socket
        self.socket.setblocking(False)  # async send and receive
        self.address = address          # (IPAddress, Port)
        ### --- ###

        ### Thread ###
        threading.Thread.__init__(self)
        self.name = user_data["name"]
        ### --- ###

        ### Logging ###
        logging.getLogger("PIL").setLevel(logging.WARNING)  # disable PIL library logging
        self.log = logging.getLogger(
            self.name + '_{}_{}'.format(*self.address)
        )
        ### --- ###

        ### Omnia Protocol and Class ###
        self.loop = asyncio.new_event_loop()    # asyncio loop object
        self.omniaClass = OmniaClass(self.log, user_data)   # new instance of OmniaClass for this user
        self.reader = None      # asyncio StreamReader object
        self.writer = None      # asyncio StreamWriter object
        ### --- ###

        ### Omnia Controller ###
        self.omniaController = omniaController
        ### --- ###

        ### User Data ###
        '''
        user_data structure
        {
            "name": "user_name",
            "uid": "user id"    # RFID or BLE
        }
        '''
        self.user_data = user_data
        ### --- ###

        ### Applications ###
        self.applications = []       # list of apps objects
        self.applications_name = []  # list of apps names
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
    def initConfig(self):
        self.omniaClass.getPinConfig(self.name + "/src/config/pinout.json")
        self.omniaClass.getConfig(self.name + "/src/config/config.json")

    # watch startup
    async def initConnection(self):    
        # send user profile pic
        pic = Image.open(self.name + "/src/images/pic.png")
        self.omniaClass.setImg(pic)
        self.omniaClass.sendImg()
        await asyncio.sleep(3)

        # send Omnia version
        self.omniaClass.newImg()
        self.omniaClass.setText((10,0),"OMNIA", 255,self.omniaClass.getFonts()[1])
        self.omniaClass.setText((18,32),"V "+ self.omniaClass.getVersion(), 255, self.omniaClass.getFonts()[1])
        self.omniaClass.sendImg()
        # await asyncio.sleep(3)

        userAppsPath = self.name + "/src/"    # path to user apps

        # create list of files in src's user path
        apps = []
        if os.path.exists(userAppsPath):
            for (_, _, filenames) in os.walk(userAppsPath):
                apps.extend(filenames)
                break
    
        apps.sort()     # sort in alphabetical order

        self.prepareApps(apps)
    
    def prepareApps(self, apps):
        for app in apps:
            app_name = app[:-3]     # remove .py extension
            if app_name[0] != "_":      # do not import apps that start with "_"
                self.log.debug("loading app: {!r}".format(app_name.upper()))
                AppObj = getattr(importlib.import_module(self.name + ".src." + app_name), app_name.capitalize())    # import App class
                self.applications.append(AppObj(self.name, self.omniaClass, self.omniaController))      # create App instance
                self.applications_name.append(app_name.upper())     # append app name
            else:
                self.log.debug("ignoring app: {!r}".format(app_name[1:].upper()))

    async def runApps(self):
        await asyncio.sleep(6)
        self.log.debug("loading MENU")
        Menu = getattr(importlib.import_module(self.name + ".menu"), "Menu")  # import Menu class
        menu = Menu(self.omniaClass, self.applications_name)    # create Menu instance
        
        i = 0   # index of app to run (-1 = Menu) from self.applications list
        self.log.debug("starting app: {!r}".format(self.applications_name[i]))

        while self.omniaClass.isAlive():
            if i == -1:
                self.log.debug("starting MENU")
                i = await menu.run()    # start menu and finally get selected app index
                self.log.debug("exited MENU")
                self.log.debug("starting app: {!r}".format(self.applications_name[i]))
            else:
                running_app = self.applications_name[i]     # currently running app
                i = await self.applications[i].run()    # start app and finally get selected app index
                self.log.debug("exited {!r}".format(running_app))
                if i != -1:
                    self.log.debug("starting app: {!r}".format(self.applications_name[i]))

    def run(self):

        # generate asyncio socket interfaces: 
        #   reader <-> receive
        #   writer <-> send 
        self.reader, self.writer = self.loop.run_until_complete(asyncio.open_connection(sock=self.socket))
        self.omniaClass.setSendFunction(self.send)  # set omniaClass send function
        
        # initialize configuration of pins and settings
        self.initConfig()

        # create receive task
        recv_task = self.loop.create_task(self.recv())  

        # run initConnection as a task
        self.loop.create_task(self.initConnection())   

        # create task to run the apps
        apps_task = self.loop.create_task(self.runApps())

        ### Notification ###
        notifyService = NotifyService(self.omniaClass, self.omniaController, self.log)   # create NotifyService instance
        notify_service_task = self.loop.create_task(notifyService.run())   # create task to run the notify service
        ### --- ###

        try:
            self.loop.run_forever()     # run tasks continuously
        except KeyboardInterrupt:   # stop if Ctrl-C
            self.log.debug("closing {!r} thread".format(self.name))
            pass

        self.loop.close()   # stop tasks and close loop

    def resumeConnection(self, socket):
        self.socket = socket
        self.omniaClass.getPinConfig(self.name + "/src/config/pinout.json")
        self.omniaClass.resumeImg()
        self.log.debug("resumed")
