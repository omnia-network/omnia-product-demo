import asyncio
import numpy

class Devices:

    def __init__(self, username, omniacls, omnia_controller):
        self.username = username
        self.omniacls = omniacls
        self.omnia_controller = omnia_controller

        self.changed = True
        self.close_app = False
        
        self.n = int(self.omniacls.width/10)-1

        self.devices = []
        self.i = 0

        self.changed = True
        self.next_app = False
        self.close_app = False

        self.page = 1

    def clickCallback(self, clickedBtn):

        self.changed = True

        if(clickedBtn == "SELECT"):
            if (self.i == len(self.devices)):
                self.close_app = True
            else:
                device = self.devices[self.i]
                print(device.name)
                devType = device.getDeviceType()
                iot_function = self.omnia_controller.getIOTFunction(self.username, devType)
                iot_function.handleStreaming(device)
                device.runIOTFunction(iot_function)

        elif(clickedBtn == "DOWN"):
            if(self.i == len(self.devices)):    # go down until "MENU"
                self.i = 0
            else:
                self.i += 1

            self.page = int(self.i/self.n) + 1
                
        elif(clickedBtn == "UP"):
            if(self.i == 0):
                self.i = len(self.devices)  # go to "MENU"
            else:
                self.i -= 1

            self.page = int(self.i/self.n) + 1


    async def run(self):

        self.omniacls.setButtonCallback(self.clickCallback)

        self.changed = True		

        while((not self.close_app) and self.omniacls.isAlive()):
            self.devices = await self.omnia_controller.listNearDevices(self.username)
            pages = int(numpy.ceil(len(self.devices) / self.n))
            if pages == 0: pages = 1
            
            if self.changed:
                self.omniacls.newImg()
                self.omniacls.setText((45,0),"DEVICES "+str(self.page)+"\\"+str(pages), 255,self.omniacls.getFonts()[0])
                self.omniacls.setText((1,10+(self.i%self.n)*10),">", 255,self.omniacls.getFonts()[0])
                # self.omniacls.setText((10,10),self.devices[self.n*(self.page-1)], 255,self.omniacls.getFonts()[0])
                for x in range(0,self.n-1):
                    if((self.page-1)*self.n+x+1 < len(self.devices)):
                        self.omniacls.setText((10,10+(x+1)*10),self.devices[(self.page-1)*self.n+x+1].name, 255,self.omniacls.getFonts()[0])
                if self.page == pages:
                    self.omniacls.setText((10, 10 + len(self.devices) % self.n * 10), "MENU", 255, self.omniacls.getFonts()[0])

                self.omniacls.sendImg()
                self.changed=False
    
            await asyncio.sleep(0.1)

        self.close_app = False
        return -1


