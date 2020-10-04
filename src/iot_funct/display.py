from PIL import Image, ImageDraw, ImageFont
import io
import asyncio

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
        self.img = Image.new("RGB", (self.width,self.height))
        self.font = ImageFont.truetype('Arial.ttf', 40)
        self.draw = ImageDraw.Draw(self.img)

        ## touch
        self.x = 0
        self.y = 0

        self.old_y = 0

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
            self.x = int(s_x)
            self.y = int(s_y)
            print(self.x, self.y)
            self.scale_coords()
            print(self.x, self.y)
    
    def scale_coords(self):
        scaled_x = int( self.x * (self.height/240))
        scaled_y = int( self.y * (self.width/320))
        self.x = abs( scaled_y - self.width)
        self.y = abs( scaled_x - self.height)

    def send_img(self):
        self.img.rotate(90, expand=True)

        self.device.omniacls.sendDisplay(self.img)

    def start(self):
        self.device.omniacls.startRecvTouch(self.touchCallback)
        self.img.paste((0,0,0), [0,0,self.width,self.height])

        self.send_img()
    
    def run(self):

        if self.device:
            if self.y != self.old_y:
                self.old_y = self.y
                self.img.paste((0,0,0), [0,0,self.width,self.height])
                r = 10
                self.draw.ellipse([(self.x-r, self.y-r), (self.x+r, self.y+r)], fill=(255,0,0))
                self.draw.text((10,60), str(self.x)+","+str(self.y), font=self.font, fill=(255,255,255,255))

                self.send_img()
    