import asyncio
import cv2
from PIL import Image

class Video():

    def __init__(self, omniacls):
        self.omniacls=omniacls

        self.close_app = False

        self.pause = False
    
    def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            self.close_app = True
        
        elif(clickedBtn == "DOWN"):
            self.pause = True
            
        elif(clickedBtn == "UP"):
            self.pause = False

    async def run(self):

        self.omniacls.setButtonCallback(self.clickCallback)

        vidcap = cv2.VideoCapture('src/video/gaber.mp4')
        success,image = vidcap.read()
        count = 0

        self.pause = False
        self.drawnPause = False
        
        while((not self.close_app) and self.omniacls.isAlive()):
            
            if not self.pause:
                im=Image.fromarray(image)
                im=im.rotate(90, expand=True)
                im=im.resize((128,64))
                im=im.convert('1')
                self.omniacls.setImg(im)
                self.omniacls.sendImg()
                success,image = vidcap.read()
                count+=1
            else:
                self.omniacls.newImg()
                self.drawPause()
                self.omniacls.sendImg()
            
            await asyncio.sleep(0.1)

        self.close_app = False

        return -1
    
    def drawPause(self):
        x0 = 48
        y0 = 12
        x1 = 56
        y1 = 52
        self.omniacls.d.rectangle((x0, y0, x1, y1), fill="white")

        x0 = 72
        x1 = 80
        self.omniacls.d.rectangle((x0, y0, x1, y1), fill="white")
