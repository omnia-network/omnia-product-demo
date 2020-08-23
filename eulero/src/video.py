import asyncio
import cv2
from PIL import Image

class Video():

    def __init__(self, omniacls):
        self.omniacls=omniacls

        self.close_app = False
    
    def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            self.close_app = True
        
        '''elif(clickedBtn == "DOWN"):
            
                
        elif(clickedBtn == "UP"):'''

    async def run(self, firstApp=-1):

        self.omniacls.setButtonCallback(self.clickCallback)

        vidcap = cv2.VideoCapture('src/video/gaber.mp4')
        success,image = vidcap.read()
        count = 0
        
        while((not self.close_app) and self.omniacls.isAlive()):
            
            im=Image.fromarray(image)
            im=im.rotate(90, expand=True)
            im=im.resize((128,64))
            im=im.convert('1')
            self.omniacls.setImg(im)
            self.omniacls.sendImg()
            success,image = vidcap.read()
            count+=1
                    
            
            await asyncio.sleep(0.1)

        self.close_app = False

        return -1
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    