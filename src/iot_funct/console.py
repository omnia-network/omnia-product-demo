import time
import os
import asyncio

class Console():
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        self.sharing = self.omnia_controller.omnia_media_sharing
        self.counter = 0
        self.started = False
        self.deviceChanged = True
        self.old_len = 0
        self.text = ''
        self.ris = ''
        self.currDir="demo/"

    def getNotificationMessage(self, deviceName, username=None):

        msg = []

        msg.append([(10, 35), deviceName.replace("_", " ").upper()])
        msg_status = "START STREAM?"
        
        msg.append([(10,50), msg_status])

        return msg
    
    def handleStreaming(self, device):
        if self.device!=device:
            #print("setting new device", self.device, device)
            old_device = self.device
            self.__setDevice(device)
            self.deviceChanged = True
            if old_device != 0:
                old_device.omniacls.newImg()
                old_device.omniacls.sendImg()
                old_device.resetStreamingUser()
    
    def __setDevice(self, device):
        self.device = device
    
    def start(self):
        pass
    
    def run(self):

        if self.device:

            text = self.sharing.getText(self.username)

            if self.old_len != len(text) or self.deviceChanged:
                self.deviceChanged=False
                self.old_len = len(text)
                self.text = text
                if len(text) != 0:
                    key = text[len(text)-1]
                        
                    if key == '\r':
                        if self.text[:-1] == 'clear':
                            self.ris = ''
                        elif ("cd" in self.text[:-1]):
                            self.ris=""
                            directory=self.text[:-1].split(" ")[1]
                            if(directory==".."):
                                if(self.currDir!="demo/"):
                                    st=self.currDir.split("/")
                                    self.currDir="/".join(st[:-2])+"/"
                            elif(directory!="."):
                                if(directory in os.listdir(self.currDir)):
                                    self.currDir+=directory+"/"
                                else:
                                    self.ris=directory+" not found"
                            
                        else:
                            stream = os.popen("cd "+self.currDir+" && "+self.text[:-1])
                            self.ris = stream.read()
                            stream.close()
                        self.text = ''
                        self.sharing.setText('', self.username)
                    
                self.device.omniacls.newImg()
                self.device.omniacls.setText((35,0),"CONSOLE ", 255,self.device.omniacls.getFonts()[0])
                self.device.omniacls.setText((1,10), "~"+self.currDir.replace("demo", "")[:-1]+" $ "+self.text, 255,self.device.omniacls.getFonts()[0])
                
                self.device.omniacls.setText((10,30), self.ris, 255,self.device.omniacls.getFonts()[0])
                self.device.omniacls.sendImg()
    