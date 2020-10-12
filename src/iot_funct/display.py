from PIL import Image, ImageDraw, ImageFont
import io
import asyncio
import time
import json

from src.omniaUI    import OmniaUI, OmniaUIElement

class Display:
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        self.sharing = self.omnia_controller.omnia_media_sharing
        self.deviceChanged = True

        self.width = 320
        self.height = 240
        self.ui = OmniaUI( (self.width, self.height), click_callback=self.clickCallback, debug=True )

        ## touch
        self.x = 0
        self.y = 0

        self.old_y = 0

        self.count = 0

        self.refresh_timeout = 1  # seconds
        self.time = time.time()

        self.volume = 5

        # UI elements
        self.song_time = None
        self.song_duration = None
        self.dot = None
        self.song_name = None
        self.cover = None
        self.text_volume = None

        with open("src/iot_funct/resources/playlist.json", "r") as p:
            self.playlist = json.load(p)
        
        self.pl_index = "0"
        
        # song parameters
        self.song_length = 1
        self.elapsed_seconds = 0
        self.pause = True

    def getNotificationMessage(self, deviceName, username=None):

        msg = []

        msg.append([(10, 35), deviceName.replace("_", " ").upper()])
        msg_status = "START STREAM?"
        
        msg.append([(10,50), msg_status])

        return msg
    
    def handleStreaming(self, device):
        if self.device!=device:
            #print("setting new device", self.device, device)
            if self.device != 0:
                self.stop()
            old_device = self.device
            self.__setDevice(device)
            self.deviceChanged = True
            if old_device != 0:
                
                #old_device.omniacls.newImg()
                #old_device.omniacls.sendImg()
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
        #self.count += 1
        if button.id == "play":
            button.visible = False
            pause = self.ui.getElement("pause")
            pause.visible = True
            self.pause = False
            self.sharing.setAttribute(self.username, "pause", False)
        elif button.id == "pause":
            button.visible = False
            play = self.ui.getElement("play")
            play.visible = True
            self.pause = True
            self.sharing.setAttribute(self.username, "pause", True)
        
        elif button.id == "prev":
            self.elapsed_seconds = 0
                
            self.sharing.setAttribute(self.username, "prev", True)

            x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
            self.dot.setPosition((x,175))

            self.ui.refresh_image()
            self.send_img()

        elif button.id == "next":
            self.elapsed_seconds = 0
                
            self.sharing.setAttribute(self.username, "next", True)

            x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
            self.dot.setPosition((x,175))

            self.ui.refresh_image()
            self.send_img()
        
        elif button.id == "vup":
            if self.volume < 10:
                self.volume += 1
                self.text_volume.setText(str(self.volume))
                self.sharing.setAttribute( self.username, "volume", self.volume)

        elif button.id == "vdown":
            if self.volume > 0:
                self.volume -= 1
                self.text_volume.setText(str(self.volume))
                self.sharing.setAttribute( self.username, "volume", self.volume)

        #self.label.setText("count: "+str(self.count))
        self.ui.refresh_image()
        self.send_img()
        print("button '{}' clicked".format(button.id))

    def send_img(self):
        img = self.ui.get_image()
        img=img.convert("RGB")
        #img.rotate(90, expand=True)

        self.device.omniacls.sendDisplay(img)

    def setSongInfo(self):
        self.song_title = self.playlist[self.pl_index]["name"]
        self.song_author = self.playlist[self.pl_index]["author"]
        self.song_cover = self.playlist[self.pl_index]["cover"]

        self.song_name.setText(self.song_title+" - "+self.song_author)

        img = Image.open(self.song_cover)
        img = img.convert("RGBA")
        img = img.resize((160,160))
        self.cover.addImage(img)

    def start(self):
        self.device.omniacls.startRecvTouch(self.touchCallback)
        self.ui.clear_image()

        self.ui.loadFromXMLFile("src/iot_funct/resources/home.xml")

        self.song_time = self.ui.getElement("song-time")
        self.song_duration = self.ui.getElement("song-duration")
        self.dot = self.ui.getElement("circle")

        self.song_name = self.ui.getElement("song-name")
        self.cover = self.ui.getElement("cover")

        self.text_volume = self.ui.getElement("vlevel")

        x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
        self.dot.setPosition((x,175))       

        self.setSongInfo()

        self.send_img()

        self.time = time.time()
    
    def stop(self):
        self.ui.clear_image()
        self.send_img()  

    def run(self):

        if self.device:

            if time.time() - self.time > self.refresh_timeout:
                self.time = time.time()

                index = self.sharing.getAttribute(self.username, "song_id")
                if index:
                    if index != self.pl_index:
                        self.pl_index = index
                        self.setSongInfo()

                # display song lenght
                self.song_length = self.sharing.getAttribute(self.username, "duration")
                if self.song_length:
                    duration = "{}:{:02}".format( int(self.song_length) // 60, int(self.song_length) % 60 )
                    self.song_duration.setText(duration)
                else:
                    self.song_length = 1

                self.elapsed_seconds = self.sharing.getAttribute(self.username, "elapsed_time")
                if not self.elapsed_seconds:
                    self.elapsed_seconds = 0
                
                if not self.pause:
                    self.song_time.setText("{}:{:02}".format(int(self.elapsed_seconds) // 60, int(self.elapsed_seconds) % 60))
                    
                    x = int(self.elapsed_seconds * ((self.width - 18)/self.song_length))
                    self.dot.setPosition((x,175))

                self.ui.refresh_image()
                self.send_img()

            '''if self.y != self.old_y:
                self.old_y = self.y
                self.ui.refresh_image()
                self.send_img()'''
    