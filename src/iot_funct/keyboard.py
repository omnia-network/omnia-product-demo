import asyncio

class Keyboard():
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        self.sharing = self.omnia_controller.omnia_media_sharing

        self.c = b''
        self.text = ''

    def getNotificationMessage(self, deviceName, username=None):

        msg = []

        msg.append([(10, 35), deviceName.replace("_", " ").upper()])
        msg_status = "ENABLE KEYBOARD?"
        
        msg.append([(10,50), msg_status])

        return msg

    def handleStreaming(self, device):
        if self.device!=device:
            old_device = self.device
            self.__setDevice(device)
            self.deviceChanged = True
            if old_device != 0:
                old_device.resetStreamingUser()
    
    def __setDevice(self, device):
        self.device = device
    
    def I2CCallback(self, character):
        if character != self.c:
            self.c = character

            if self.c != b'\x00':
                if self.c != b'\x7f': #backspace
                    self.sharing.addToText(self.c.decode(), self.username)
                else:
                    self.sharing.removeFromText(1, self.username)

    def start(self):
        self.device.omniacls.setI2C()
        self.device.omniacls.startRecvI2C(self.I2CCallback, 8, 1)

    def run(self):
        #print(self.c, self.old_c)
        pass
