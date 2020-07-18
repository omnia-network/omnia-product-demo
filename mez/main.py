from mez.src.menu  		import Menu
from mez.src.clock 		import Clock
from mez.src.torch 		import Torch
from mez.src.weather	    import Weather
from mez.src.settings 	import Settings
from PIL   			import Image
import time
import threading

class Main(threading.Thread):
    def __init__(self, app):
        self.app=app
        threading.Thread.__init__(self)
    
    def run(self):
        self.app.getPinConfig("mez/src/config/pinout.json")
        self.app.getConfig("mez/src/config/config.json")
        pic=Image.open('mez/src/images/pic.png')
        self.app.setImg(pic)
        self.app.sendImg()
        for _ in range(100):
            self.app.recvData()

        self.app.newImg()
        self.app.setText((10,0),"GBROS", 255,self.app.getFonts()[1])
        self.app.setText((32,32),"V 0.1", 255,self.app.getFonts()[1])
        self.app.sendImg()
        for _ in range(100):
            self.app.recvData()

        applications=[["CLOCK", Clock(self.app)],["TORCH", Torch(self.app)],["WEATHER", Weather(self.app)],["SETTINGS",Settings(self.app)]]
        menu=Menu(self.app, applications)
        applications[0][1].run(menu)

    def resumeConnection(self, so):
        self.app.changeSocket(so)
        self.app.getPinConfig("mez/src/config/pinout.json")
        self.app.dead=False

