from PIL import Image, ImageDraw, ImageFont
import io
import asyncio
import time

from src.omniaUI    import OmniaUI, OmniaUIElement

class Display:
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        #self.sharing = self.omnia_controller.omnia_media_sharing
        self.deviceChanged = True
        
        self.text = ''

        self.width = 320
        self.height = 240
        self.ui = OmniaUI( (self.width, self.height), click_callback=self.clickCallback, debug=True )

        ## touch
        self.x = 0
        self.y = 0

        self.old_y = 0

        self.count = 0

        self.refresh_timeout = 2  # seconds
        self.time = time.time()

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
    
    def touchCallback(self, data):
        s_coords = ['0', '0']
        if len(data) > 0:
            s_coords = data.split(',')
        
        s_x = s_coords[0]
        s_y = s_coords[1]

        if s_x != '0' and s_y != '0':
            x = int(s_x)
            y = int(s_y)
            #print(self.x, self.y)
            self.x, self.y = self.scale_coords(x,y)
            #print(self.x, self.y)
            self.ui.click((self.x, self.y))
    
    def scale_coords(self, x, y):
        scaled_x = int( x * (self.height/240))
        scaled_y = int( y * (self.width/320))
        r_x = abs( scaled_y - self.width)
        r_y = abs( scaled_x - self.height)

        return r_x, r_y
    
    def clickCallback(self, button):
        #button.setText("count")
        self.count += 1
        self.label.setText("count: "+str(self.count))
        self.ui.refresh_image()
        self.send_img()
        print("button '{}' clicked".format(button.id))

    def send_img(self):
        img = self.ui.get_image()
        img=img.convert("RGB")
        #img.rotate(90, expand=True)

        self.device.omniacls.sendDisplay(img)

    def start(self):
        self.device.omniacls.startRecvTouch(self.touchCallback)
        self.ui.clear_image()

        self.button = OmniaUIElement("btn", "button", (10,10), "click me", clickable=True)

        self.label = OmniaUIElement("lbl", "label", (10,50), "count: 0", background_color=self.ui.background_color, outline_color=self.ui.background_color)

        self.ui.addElement(self.button)
        self.ui.addElement(self.label)
        self.ui.refresh_image()

        self.send_img()
    
    def run(self):

        if self.device:
            #if self.y != self.old_y:
                #self.old_y = self.y
                #self.ui.clear_image()
            if time.time() - self.time > self.refresh_timeout:
                self.time = time.time()
                self.ui.refresh_image()
                self.send_img()
    