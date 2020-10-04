# install opencv: https://stackoverflow.com/a/60201245/5094892
# run python3: LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1 python3
import cv2
from PIL import Image
import io

class Screen():
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        
        self.vidcap = cv2.VideoCapture('src/video/gaber.mp4')
        self.success = None
        self.image = None
        self.count = 0
        
        ## touch
        self.x = 0
        self.y = 0

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

    def touchCallback(self, data):
        s_coords = ['0', '0']
        if len(data) > 0:
            s_coords = data.split(',')
        
        s_x = s_coords[0]
        s_y = s_coords[1]

        if s_x != '0' and s_y != '0':
            try:
                self.x = int(s_x)
                self.y = int(s_y)
                print(self.x, self.y)
            except:
                pass

    def start(self):
        self.device.omniacls.startRecvTouch(self.touchCallback)

        self.success, self.image = self.vidcap.read()
        self.count = 0

        self.device.omniacls.startStream()
    
    def run(self):        

        if self.device:

            if self.success:
                if self.y < 150:
                    im=Image.fromarray(self.image)
                    im=im.rotate(270, expand=True)
                    im=im.resize((320,240))

                    self.device.omniacls.sendFrame(im)

                    for _ in range(2):
                        self.success, self.image = self.vidcap.read()
                        self.count += 1
                else:
                    self.device.omniacls.sendFrame(None)
            else:
                self.device.omniacls.stopStream()
