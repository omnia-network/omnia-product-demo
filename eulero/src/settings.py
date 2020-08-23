import asyncio

class Settings:
    def __init__(self, omniacls):
        self.omniacls=omniacls
        self.contrast=0
        self.rotation=0
        self.i = 0
        self.changed=True
        self.close_app=False
    
    def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            if(self.i==2):
                self.close_app=True
            elif(self.i==1):
                self.rotation = not self.rotation
                self.omniacls.setRotation(self.rotation)
                self.changed=True
            elif(self.i==0):
                self.contrast = not self.contrast
                self.omniacls.setContrast(self.contrast)
                self.changed=True
        
        elif(clickedBtn == "DOWN"):
            if(self.i==2):
                self.i=0
            else:
                self.i+=1

            self.changed=True
            
        elif(clickedBtn == "UP"):
            if(self.i==0):
                self.i=2
            else:
                self.i-=1
            
            self.changed=True

    async def run(self):

        self.omniacls.setButtonCallback(self.clickCallback)

        self.changed=True
        self.close_app=False
        
        while((not self.close_app) and self.omniacls.isAlive()):
            if (self.changed):
                self.changed=False
                self.omniacls.newImg()

                self.omniacls.setText((35,0), "SETTINGS ", 255,self.omniacls.getFonts()[0])
                self.omniacls.setText((10,10),"CONTRAST ", 255,self.omniacls.getFonts()[0])
                self.omniacls.setText((10,20),"ROTATION ", 255,self.omniacls.getFonts()[0])
                self.omniacls.setText((10,30),"MENU ", 255,self.omniacls.getFonts()[0])
                self.omniacls.setText((1,10+self.i*10),">", 255,self.omniacls.getFonts()[0])
                
                self.omniacls.sendImg()
            
            await asyncio.sleep(0.1)

        self.close_app = False

        return -1



