import asyncio

class Torch:
    def __init__(self, username, omniacls, omnia_controller):
        self.username = username
        self.omniacls = omniacls
        self.omnia_controller = omnia_controller
        
        self.ledstatus=0
        self.npstatus=0

        self.changed = True
        self.close_app = False

        self.i = 0
        self.j = 0

        self.color_picker = False
        self.second_column = False

        self.red=0
        self.green=0
        self.blue=0

    def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            if self.color_picker:
                if self.second_column:
                    self.second_column = False
                else:
                    if self.j==3:
                        self.omniacls.setNeopixel([self.red, self.green, self.blue])
                    elif self.j==4:
                        self.red = 0
                        self.green = 0
                        self.blue = 0
                        self.omniacls.setNeopixel([self.red, self.green, self.blue])
                    elif self.j==5:
                        self.color_picker = False
                        self.j=0
                    else:
                        self.second_column = True
            else:
                if(self.i==2):
                    self.close_app=True
                elif(self.i==1):
                    self.ledstatus = not self.ledstatus
                    self.omniacls.setOutPin(16, self.ledstatus)
                elif(self.i==0):
                    self.color_picker = True

            self.changed = True
        
        elif(clickedBtn == "DOWN"):
            if self.color_picker:
                if self.second_column:
                    if self.j==0:
                        if self.red > 0:
                            self.red -=1
                    if self.j==1:
                        if self.green > 0:
                            self.green -= 1
                    if self.j==2:
                        if self.blue > 0:
                            self.blue -= 1
                else:
                    if self.j==5:
                        self.j=0
                    else:
                        self.j+=1
            else:
                if(self.i==2):
                    self.i=0
                else:
                    self.i+=1

            self.changed = True
                
        elif(clickedBtn == "UP"):
            if self.color_picker:
                if self.second_column:
                    if self.j==0:
                        if self.red < 255:
                            self.red +=1
                    if self.j==1:
                        if self.green < 255:
                            self.green += 1
                    if self.j==2:
                        if self.blue < 255:
                            self.blue += 1
                else:
                    if self.j==0:
                        self.j=5
                    else:
                        self.j-=1
            else:
                if(self.i==0):
                    self.i=2
                else:
                    self.i-=1

            self.changed = True

    async def run(self):

        self.omniacls.setButtonCallback(self.clickCallback)

        self.changed = True		
        
        self.color_picker = False
        self.second_column = False

        while((not self.close_app) and self.omniacls.isAlive()):
            if (self.changed):
                    self.changed=False
                    self.omniacls.newImg()
                    if not self.color_picker:
                        self.omniacls.setText((45,0), "TORCH ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((10,10),"TOP ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((10,20),"SIDE ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((10,30),"MENU ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((1,10+self.i*10),">", 255,self.omniacls.getFonts()[0])
                    else:
                        self.omniacls.setText((10,0),"RED ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((70,0),str(self.red), 255,self.omniacls.getFonts()[0])

                        self.omniacls.setText((10,10),"GREEN ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((70,10),str(self.green), 255,self.omniacls.getFonts()[0])

                        self.omniacls.setText((10,20),"BLUE ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((70,20),str(self.blue), 255,self.omniacls.getFonts()[0])

                        self.omniacls.setText((10,30),"SET ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((10,40),"RESET ", 255,self.omniacls.getFonts()[0])
                        self.omniacls.setText((10,50),"BACK ", 255,self.omniacls.getFonts()[0])

                        if self.second_column:
                            self.omniacls.setText((60,self.j*10),">", 255,self.omniacls.getFonts()[0])
                        else:
                            self.omniacls.setText((1,self.j*10),">", 255,self.omniacls.getFonts()[0])

                    self.omniacls.sendImg()
        
            await asyncio.sleep(0.1)

        self.close_app = False
        return -1


