import asyncio
import datetime

class Counter:
    def __init__(self, omniacls):
        self.omniacls=omniacls
        self.contrast=0
        self.rotation=0
        self.set = 0
        self.stop = 0
        self.i = 0
        self.changed=True
        self.close_app=False

    def diplayTitle(self, title, tabs):
        self.omniacls.setText((tabs*10,0), title, 255, self.omniacls.getFonts()[0])
    
    # diplay options as in the options tuple and selector
    def diplayOptions(self, options):
        for opt in options:
            self.omniacls.setText((10, opt[0]*10), opt[1], 255, self.omniacls.getFonts()[0])
        self.omniacls.setText((1, options[0][0]*10 + self.i*10), ">", 255,self.omniacls.getFonts()[0])

    def displayTitleAndOptions(self, title, tabs, options):
        self.omniacls.newImg()
        self.diplayTitle(title, tabs)  
        self.diplayOptions(options)
        self.omniacls.sendImg()
        
    def clickCallback(self, clickedBtn):
        if clickedBtn == "SELECT":
            if(self.i==1):
                if not self.set:
                    # menu
                    self.close_app=True
                    self.i = 0
                else:
                    # exit
                    self.set = 0
                    self.changed = 1
                    self.count = 0
                    self.stop = 0
                    self.i = 0

            elif(self.i==0):
                if not self.set:
                    # set counter
                    self.set = 1
                    self.changed=True
                else:
                    # stop/restart counter
                    self.stop = not self.stop
        
        elif clickedBtn == "DOWN" or clickedBtn == "UP":
            self.moveSel(self.optNow, clickedBtn)
            self.changed=True

    # move the options selector based on the number of options diplayed
    def moveSel(self, options, direction):
        if direction == "DOWN":
            if self.i == (len(options) - 1):
                self.i = 0
            else:
                self.i += 1
        elif direction == "UP":
            if self.i == 0:
                self.i = len(options) - 1
            else:
                self.i -= 1

    async def run(self):
        
        self.omniacls.setButtonCallback(self.clickCallback)
        # name of the app
        self.title = "COUNTER"
        # options tuple has to be formatted as: (line number, option name)
        self.options1 = ((1, "SET"), (2, "MENU"))
        self.options2 = ((2, "STOP / RESTART"), (3, "EXIT"))
        self.optNow = self.options1     # options now on display
        self.changed=True
        self.close_app=False
        self.count = 0

        while((not self.close_app) and self.omniacls.isAlive()):
             if (self.changed and not self.set):
                self.optNow = self.options1
                self.changed=False
                self.displayTitleAndOptions(self.title, 3, self.options1)

            elif self.changed and self.set:
                self.optNow = self.options2
                sec_old = -1
                # bug: counter equals 1 as soon as soon as is set ???
                while not self.stop and self.set:
                    now = datetime.datetime.now()
                    sec = now.second
                    if sec != sec_old:
                        self.displayTitleAndOptions(self.title + ": " + str(self.count), 0, self.options2)
                        self.count += 1
                        sec_old = sec
                    # move the selector between seconds
                    elif self.changed:
                        self.displayTitleAndOptions(self.title + ": " + str(self.count), 0, self.options2)
                    await asyncio.sleep(0.1)
                if self.stop:
                    self.displayTitleAndOptions(self.title + ": " + str(self.count), 0, self.options2)
            
            await asyncio.sleep(0.1)

        self.close_app = False

        return -1



