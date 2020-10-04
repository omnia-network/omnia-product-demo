import time
import asyncio
from numpy.random 			import randint

class NotifyService():
    def __init__(self, omniacls, omnia_controller, log):

        ### Omnia Class and Controller ###
        self.omniacls = omniacls
        self.omnia_controller = omnia_controller
        ### --- ###
        
        ### Logging ###
        self.log = log
        ### --- ###

        ### User Data ###
        self.username = self.omniacls.getUsername()
        ### --- ###

        ### Devices ###
        self.recentDevices = []
        #self.nearDeavices=[]
        self.device = 0
        ### --- ###

        ### Flags ###
        self.stop = False
        self.accepted = False
        ### --- ###
        
        self.notToResetType = ["screen", "keyboard", "console", "sound", "display"]
        self.threadType = ["screen", "keyboard", "console", "sound", "display"]

    def clickButtonCallback(self, clickedBtn):
        self.log.debug("notification clicked "+clickedBtn)
        if(clickedBtn == "SELECT"):
            self.stop = True
            self.accepted = True
        
        elif(clickedBtn == "DOWN"):
            self.stop = True
                
        elif(clickedBtn == "UP"):
            self.stop = True

    async def run(self):

        self.log.debug("Notify Service started")

        while (self.omniacls.isAlive()):
            devs = await self.omnia_controller.listNearDevices(self.username)
            
            for dev in devs: 
                if((not (dev in self.recentDevices)) and (dev.getStreamingUser()=="")):
                    dev.setStreamingUser(self.username)
                    self.device=dev

            for dev in self.recentDevices:
                if(not (dev in devs)):
                    self.recentDevices.remove(dev)

            if(self.device):
                self.omniacls.startNotify(self.clickButtonCallback)

                self.log.debug("new notification for "+self.username)

                color = list(randint(0,32,3))
                self.omniacls.setNeopixel(color, -1, True)
                self.omniacls.setText((40,0), "NOTIFY", 255,self.omniacls.getFonts()[0], True)
                self.omniacls.setText((10,20), "FOUND", 255,self.omniacls.getFonts()[0], True)

                devType = self.device.getDeviceType()

                iot_function = self.omnia_controller.getIOTFunction(self.username, devType)
                
                notifMsg = iot_function.getNotificationMessage(self.device.getName())
                #self.log.debug(notifMsg)
                for line in notifMsg:
                    self.omniacls.setText(line[0], line[1], 255,self.omniacls.getFonts()[0], True)

                self.omniacls.sendImg(True)

                self.stop = False
                self.accepted = False
                startTime = time.time()

                while(not self.stop):
                    if time.time() - startTime > 30:
                        self.stop = True
                    
                    await asyncio.sleep(0.1)

                if(self.accepted):
                    if devType in self.threadType:
                        iot_function.handleStreaming(self.device)
                        self.device.runIOTFunction(iot_function)
                    '''else:
                        self.appList[devType].run(self.device)'''
                else:
                    self.device.resetStreamingUser()

                self.omniacls.setNeopixel([0, 0, 0], -1, True)
                self.omniacls.stopNotify()
                '''if not (devType in self.notToResetType):
                    self.device.resetStreamingUser()'''
                self.device = 0
            
            await asyncio.sleep(0.1)
            
    def getUsedDevices(self):
        return self.recentDevices

