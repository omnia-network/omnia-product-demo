# install opencv: https://stackoverflow.com/a/60201245/5094892
# run python3: LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1 python3
import cv2
from PIL import Image

class Screen():
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        
        self.vidcap = cv2.VideoCapture('src/video/gaber.mp4')
        self.success = None
        self.image = None
        self.count = 0

    def getNotificationMessage(self, deviceName, username=None):

        msg = []

        msg.append([(10, 35), deviceName.replace("_", " ").upper()])
        msg_status = "START STREAM?"
        
        msg.append([(10,50), msg_status])

        return msg
    
    def handleStreaming(self, device):
        if self.device!=device:
            old_device = self.device
            self.__setDevice(device)
            if old_device != 0:
                old_device.omniacls.newImg()
                old_device.omniacls.sendImg()
                old_device.resetStreamingUser()
    
    def __setDevice(self, device):
        self.device = device
    
    def start(self):
        self.success, self.image = self.vidcap.read()
        self.count = 0
    
    def run(self):        

        if self.device:

            if self.success:
                im=Image.fromarray(self.image)
                im=im.rotate(90, expand=True)
                im=im.resize((128,64))
                im=im.convert('1')
                self.device.omniacls.setImg(im)
                self.device.omniacls.sendImg()
                self.success, self.image = self.vidcap.read()
                self.count += 1
