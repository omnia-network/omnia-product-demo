import datetime
import math
import asyncio

class Clock:
    def __init__(self, omniacls):
        self.omniacls=omniacls

        self.screenOff = False
        self.timestamp = datetime.datetime.now().timestamp()
        self.changed = True
        self.next_app = False
        self.close_app = False
        self.clock_type = "analogic"

        self.cx = int(self.omniacls.heigth/2)
        self.cy = int(self.omniacls.width/2)
        self.r = self.cy
    
    def clickCallback(self, clickedBtn):
        if(clickedBtn == "SELECT"):
            if self.screenOff:
                self.timestamp = datetime.datetime.now().timestamp()
                self.screenOff = False
                self.changed = True
            else:
                self.close_app = True
        
        elif(clickedBtn == "DOWN"):
            self.timestamp = datetime.datetime.now().timestamp()
            if self.screenOff:
                self.screenOff = False
            else:
                self.clock_type = "digital"
                
        elif(clickedBtn == "UP"):
            self.timestamp = datetime.datetime.now().timestamp()
            if self.screenOff:
                self.screenOff = False
            else:
                self.clock_type = "analogic"

    async def run(self):

        self.omniacls.setButtonCallback(self.clickCallback)

        self.changed = True
        self.timestamp = datetime.datetime.now().timestamp()

        sec_old=-1
        
        timeScreenOn = 30 # seconds

        bounding_box = [(self.cx-self.r, self.cy-self.r),(self.cx+self.r, self.cy+self.r-1)]

        old_clock_type = ""

        while((not self.close_app) and self.omniacls.isAlive()):
            now = datetime.datetime.now()
            
            hour = now.hour
            min = now.minute
            sec = now.second

            date = now.strftime("%a, %b %d %Y")

            if(now.timestamp() - self.timestamp > timeScreenOn):
                self.screenOff = True

            if(self.changed or sec!=sec_old or self.clock_type != old_clock_type):
                sec_old=sec
                old_clock_type=self.clock_type
                self.changed = False
                self.omniacls.newImg()

                if not self.screenOff:

                    if(self.clock_type=="analogic"):

                        self.omniacls.d.ellipse(bounding_box, fill = 0, outline="white")

                        #seconds
                        shape = self.needleShape(sec, self.r - 1)
                        self.omniacls.d.line(shape, fill="white", width = 1)

                        #minutes
                        shape = self.needleShape(min, self.r - 5)
                        self.omniacls.d.line(shape, fill="white", width = 1)

                        #hours
                        hour = hour if (hour<12) else (hour-12)
                        shape = self.needleShape(int((hour/12)*60), self.r - 10)
                        self.omniacls.d.line(shape, fill="white", width = 1)
                    elif(self.clock_type=="digital"):
                        self.omniacls.setText((5,7),str(hour).zfill(2)+":"+str(min).zfill(2)+":"+str(sec).zfill(2), 255,self.omniacls.getFonts()[1])
                        self.omniacls.setText((20,42), date, 255, self.omniacls.getFonts()[0])
                
                self.omniacls.sendImg()
                #data=self.omniacls.sendImg_and_recvData()
            #else:
                #data=self.omniacls.recvData()
            
            await asyncio.sleep(0.1)
        
        self.close_app = False
        return -1
                        

    def needleShape(self, angle, radius):
    
        cx = self.cx
        cy = self.cy - 1
        sx = cx
        sy = cy - radius + 2

        if angle == 30:
            sx = cx
            sy = cy + radius - 2

        if angle > 0:
            rad = (angle/30) * math.pi - math.pi/2
            m = math.tan( rad )
            if angle < 30:
                sx = int( radius / math.sqrt(1+math.pow(m,2)) ) + cx
                sy = int(  m*(sx-cx) ) + cy
            elif angle > 30:
                sx = -int( radius / math.sqrt(1+math.pow(m,2)) ) + cx
                sy = int(  m*(sx-cx) ) + cy

        #print(angle, [(cx, cy),(sx, sy)])

        return [(cx, cy),(sx, sy)]

