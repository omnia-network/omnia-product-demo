import time
from PIL import Image
import time
import asyncio

class Profile:
    def __init__(self, username, omniacls, omnia_controller):
        self.username = username
        self.omniacls = omniacls
        self.omnia_controller = omnia_controller
        
        self.close_app = False
        self.pause = False
    
    def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            self.close_app = True
        
        elif(clickedBtn == "DOWN"):
            self.pause = not self.pause
                
        elif(clickedBtn == "UP"):
            self.pause = not self.pause

    async def run(self):

        self.omniacls.setButtonCallback(self.clickCallback)

        pics = []
        pics.append(Image.open('mez/src/images/pic.png'))
        pics.append(Image.open('eulero/src/images/pic.png'))
        pics.append(Image.open('gaber/src/images/pic.png'))
        img_time = time.time()
        
        self.omniacls.setImg(pics[0])
        self.omniacls.sendImg()

        i = 1

        while((not self.close_app) and self.omniacls.isAlive()):
            if time.time() - img_time > 3 and not self.pause:
                self.omniacls.setImg(pics[i])
                self.omniacls.sendImg()
                if i < len(pics)-1:
                    i += 1
                else:
                    i = 0
            
            await asyncio.sleep(0.1)

        self.close_app = False

        return -1
