from PIL import Image, ImageDraw, ImageFont, ImageOps
import time
import json
import sys
import struct
import asyncio
import logging
import io

#from src.omniaProtocol		import OmniaProtocol

class OmniaClass:

    #*****VERSION*****#
    __version__ = "0.5.1"

    ### Display types ###
    displayTypeList= {"sh1106":0, "ssd1306":1}

    timeout=1

    def getVersion(self):
        return self.__version__

    def __init__(self, logging, userData=None, protocol=None):

        ### User data ###
        self.userData = userData
        ### --- ###

        ### Image ###
        self.heigth=0
        self.width=0
        self.fonts = [ImageFont.truetype("Arial.ttf",11),ImageFont.truetype("Arial.ttf",30)]
        self.img=Image.new("L",(self.heigth,self.width))
        self.imgOld=self.img
        self.d=ImageDraw.Draw(self.img)
        self.d.rectangle((0,0,self.heigth,self.width),fill=0)
        self.imgIsNew=False
        self.ispic=False
        ### --- ###

        ### Configuration ###
        self.confpath=0
        self.config={"contrast": 0,  "rotation": 0}
        ### --- ###

        ### Pins ###
        self.neoPins=[]
        self.inPins = {}
        self.outPins = {}
        self.pwmPins= {}
        self.I2CPins = {}
        ### --- ###

        ### Receive data ###
        self.data = None
        self.__recvType = 'button'
        self.__old_recvType = 'button'
        ### --- ###

        ### Buttons Callback ###
        self.__buttons = {}
        self.__clickedBtn = None
        self.__button_cb = None
        self.__old_button_cb = None
        #self.__oldClickedBtn = ''
        ### --- ###

        ### NFC Callback ###
        self.__nfc_cb = None
        ### --- ###

        ### BLE Callback ###
        self.__ble_cb = None
        ### --- ###

        ### ADC Callback ###
        self.__adc_cb = None
        ### --- ###

        ### Touch Callback ###
        self.__touch_cb = None
        ### --- ###

        ### Protocol ###
        self.send_fn = None

        self.stream_types = ['a', 'v', 'S', 'd', 'l']
        ### --- ###

        ### Notification ###
        self.notifyStarted = False
        ### --- ###

        ### Log ###
        self.log = logging
        ### --- ###

        ### Latency ###
        self.l_time = 0.0
        self.latency = 0.0
        self.tot_latency = 0.0
        self.latency_iterations = 10
        self.n_latency_sends = 0
        self.__latency_cb = None
        ### --- ###

        self.sc = None        

        self.alive = True
        self.recvTime = -1
    
    ''' 
    ### Send data ###
    '''

    def setSendFunction(self, send_fn):
        self.send_fn = send_fn

    def __packMessage(self, msg, msg_type):

        if not msg_type in self.stream_types:
            msg = '-'.join(map(str, msg))
            msg = msg.encode()
        
        b_msg_type = msg_type.encode()
        
        to_send = b_msg_type + msg #+ b'\n'

        #return to_send

        #self.log.debug("sending message: {}".format(to_send))

        return self.__setMsg(to_send)

    def __setMsg(self, msg):
        # Prefix each message with a 4-byte length (network byte order)
        #self.log.debug("len {!r}".format(len(msg)))
        msg = struct.pack('>I', len(msg)) + msg
        return msg

    def __send(self, msg):
        
        if (self.canSend and self.alive):
            try:
                self.send_fn(msg)
            except:
                pass
    
    def __sendc(self, msg):
        try:
            self.send_fn(msg)
        except:
            pass
    
    ''' 
    ### --- ###
    '''

    '''
    ### Receive Data ###
    '''

    def setRecvType(self, recv_type):
        self.__old_recvType = self.__recvType
        self.__recvType = recv_type
    
    def resetRecvType(self):
        self.__recvType = self.__old_recvType

    # this is the receive callback
    def receivedData(self, data):
        self.data = data

        #self.log.debug("received data of type '{}'".format(self.__recvType))

        if self.__recvType == 'button':
            self.receivedButtons(int(data))
        elif self.__recvType == 'nfc':
            self.receivedNFC(data.decode())
        elif self.__recvType == 'ble':
            self.receivedBLE(data.decode().replace('\n',''))
        elif self.__recvType == 'adc':
            self.receivedADC(int(data))
        elif self.__recvType == 'i2c':
            #self.log.debug("I2C received: {!r}".format(data.decode().replace('\n','')))
            self.receivedI2C(bytearray(data).replace(b'\n',b''))    # avoid reading '\n' at the end
        elif self.__recvType == 'touch':
            self.receivedTouch(data.decode().replace('\n',''))
        elif self.__recvType == 'latency':
            self.receivedLatency(data.decode().replace('\n',''))
    '''
    ### --- ###
    '''

    ''' 
    ### Buttons callback ###
    '''

    def setButtonCallback(self, button_cb):
        #self.__oldClickedBtn = ''
        self.__button_cb = button_cb
    
    def receivedButtons(self, data):
        self.__clickedBtn = None
        for pin in self.inPins:
            if(data & 1<<self.inPins[pin]["number"]):
                self.__buttons[pin]=1
                self.__clickedBtn = pin
            else:
                self.__buttons[pin]=0
        
        if self.__clickedBtn:
            self.log.debug("clicked {!r}".format(self.__clickedBtn))
            self.__button_cb(self.__clickedBtn)
    
    '''
    ### --- ###
    '''

    '''
    ### Latency ###
    '''

    def sendLatencyMessage(self):
        self.l_time = time.time()
        self.__sendc(self.__packMessage(str(self.l_time).encode(), 'l'))
        self.n_latency_sends += 1

    def calculateLatency(self, iterations=10, future=None):
        self.sendLatencyMessage()
        self.latency_iterations = iterations
        self.setRecvType('latency')
        self.__latency_cb = future
        self.log.debug("calculating latency...")

    def receivedLatency(self, response):
        if response != '':
            self.tot_latency += (time.time() - float(response)) / 2
            
            if self.n_latency_sends == self.latency_iterations:

                self.latency = (self.tot_latency / self.n_latency_sends) * 1000

                self.n_latency_sends = 0

                self.log.debug("latency: {} ms".format(self.latency))
                if self.__latency_cb:
                    self.__latency_cb.set_result(self.latency)
            else:
                self.sendLatencyMessage()
    
    def getLatency(self):
        if self.latency > 0:
            return self.latency

    '''
    ### --- ###
    '''

    '''
    ### Pins ###
    '''

    def setInPins(self):
        for pin in self.inPins:
            self.setInPin(self.inPins[pin]['number'])

    def setNeoPin(self, pin):
        if not (pin in self.neoPins):
            self.neoPins.append(pin)

    def setOutPin(self, pin, value, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__send(self.__packMessage([
                pin, 
                int(not value)
                ], 'O'))

    def setInPin(self, pin, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__sendc(self.__packMessage([
                pin
                ], 'I'))

    def setPwm(self, pin, freq, duty, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__send(self.__packMessage([
                pin, 
                freq, 
                duty
                ], 'P'))
    
    def setNeopixel(self, status, pin=-1, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):

            if pin == -1:
                if(len(self.neoPins)):
                    pin = self.neoPins[0]
                else:
                    self.log.debug("neopixel pin not specified")
                    return
            else:
                if not pin in self.neoPins:
                    self.neoPins.append(pin)
                
            self.__send(self.__packMessage([
                pin, 
                status[0], 
                status[1], 
                status[2]
                ], 'N'))
    
    '''
    ### --- ###
    '''

    '''
    ### Display ###
    '''

    def setDisplay(self, sda, scl, heigth, width, dispType, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.heigth = heigth
            self.width = width
            disp=self.displayTypeList[dispType]
            self.__sendc(self.__packMessage([
                sda,
                scl,
                heigth,
                width,
                disp
                ], 'D'))

    '''
    ### --- ###
    '''

    '''
    ### Touchscreen ###
    '''
    def startRecvTouch(self, callback):
        self.setRecvType('touch')
        self.__touch_cb = callback
    
    def stopRecvTouch(self, callback):
        self.resetRecvType()
        self.__touch_cb = None
    
    def receivedTouch(self, data):
        self.__touch_cb(data)
    '''
    ### --- ###
    '''

    ''' 
    ### NFC functions and callback ###
    '''

    def setNFC(self, sclk, mosi, miso, rst, sda, notify=True):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__sendc(self.__packMessage([
                sclk,
                mosi,
                miso,
                rst,
                sda
                ], 'n'))

    def startRecvNFC(self, nfc_cb):
        self.__send(self.__packMessage([
            1
        ], 'f'))
        self.__nfc_cb = nfc_cb
        self.setRecvType('nfc')
    
    def stopRecvNFC(self):
        self.__send(self.__packMessage([
            0
        ], 'f'))
        self.__nfc_cb = None
        self.resetRecvType()

    def setNFCCallback(self, nfc_cb):
        self.__nfc_cb = nfc_cb
    
    def receivedNFC(self, data):
        self.__nfc_cb(data)
    
    '''
    ### --- ###
    '''

    ''' 
    ### BLE functions and callback ###
    '''

    def setBLE(self, notify=True):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__sendc(self.__packMessage([
                1
                ], 'B'))

    def startRecvBLE(self, ble_cb):        
        self.__send(self.__packMessage([
            1
        ], 'b'))            # start BLE scan
        self.__ble_cb = ble_cb
        self.setRecvType('ble')
        self.log.debug("starting BLE scan")
    
    def stopRecvBLE(self):
        self.__send(self.__packMessage([
            0
        ], 'b'))
        self.__ble_cb = None
        self.resetRecvType()
        self.log.debug("stopping BLE scan")

    def setBLECallback(self, ble_cb):
        self.__ble_cb = ble_cb
    
    def receivedBLE(self, data):
        self.__ble_cb(data)
    
    '''
    ### --- ###
    '''

    ''' 
    ### AUDIO functions and callback ###
    '''

    def startAudio(self, framerate, channels, sampwidth, chunk_size, notify=True):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__sendc(self.__packMessage([
                1, 
                framerate, 
                channels, 
                sampwidth, 
                chunk_size
                ], 'A'))
    
    def stopAudio(self, notify=True):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__sendc(self.__packMessage([
                0
                ], 'A'))

    '''def setAudio(self, bck, ws, sdout, samplerate, notify=True):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.__sendc(self.__packMessage([
                bck, 
                ws, 
                sdout, 
                samplerate
                ], 'J'))'''
    
    def sendAudio(self, samples):
        self.__send(self.__packMessage(samples, 'a'))
    '''
    ### --- ###
    '''

    ''' 
    ### ADC functions and callback ###
    '''

    def startRecvADC(self, adc_cb, pin):
        self.__adc_cb = adc_cb
        self.setRecvType('adc')
        self.__send(self.__packMessage([
            1,
            pin
        ], 'A'))
    
    def stopRecvADC(self):
        self.__send(self.__packMessage([
            0
        ], 'A'))
        self.__adc_cb = None
        self.resetRecvType()

    def setADCCallback(self, adc_cb):
        self.__adc_cb = adc_cb
    
    def receivedADC(self, data):
        self.__adc_cb(data)
    
    '''
    ### --- ###
    '''

    '''
    ### I2C functions and callback ###
    '''

    def setI2C(self, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.log.debug("setting I2C")
            sda = self.I2CPins["sda"]
            scl = self.I2CPins["scl"]
            self.__send(self.__packMessage([
                sda,
                scl,
                ], 'i'))
    
    def startRecvI2C(self, i2c_cb, addr, nbytes):
        self.__i2c_cb = i2c_cb
        self.setRecvType('i2c')
        self.log.debug("start receiving I2C")
        self.__send(self.__packMessage([
                1,
                addr,
                nbytes
                ], 'c'))
    
    def stopRecvI2C(self):
        self.log.debug("stop receiving I2C")
        self.__send(self.__packMessage([
                0
                ], 'c'))
        self.__i2c_cb = None
        self.resetRecvType()

    def setI2CCallback(self, i2c_cb):
        self.__i2c_cb = i2c_cb
    
    def receivedI2C(self, data):
        self.__i2c_cb(data)
    
    '''
    ### --- ###
    '''
    
    '''
    ### User data ###
    '''

    def setUserData(self, userData):
        self.userData = userData
    
    def getUsername(self):
        return self.userData["name"]
    
    def getUid(self):
        if "uid" in self.userData:
            return self.userData["uid"]

    '''
    ### --- ###
    '''
    
    '''
    ### Configuration ###
    '''

    def getPinConfig(self, path):
        with open(path, "r") as rf:
            tmp = json.load(rf)
            self.inPins = tmp["in"]
            self.outPins = tmp["out"]
            self.setInPins()

            needed = True

            if ("config" in tmp):
                needed = tmp["config"]["needed"]

            if needed:
                if("pwm" in tmp):
                    self.pwmPins= tmp["pwm"]

                if ("neopixel" in tmp):
                    for neo in tmp["neopixel"]:
                        self.setNeoPin(tmp["neopixel"][neo]["number"])

                if ("display" in tmp):
                    self.heigth=tmp["display"]["heigth"]
                    self.width=tmp["display"]["width"]
                    self.setDisplay(tmp["display"]["sda"], tmp["display"]["scl"], self.heigth, self.width, tmp["display"]["type"])

                if ("nfc" in tmp):
                    self.setNFC(tmp["nfc"]["sclk"],tmp["nfc"]["mosi"],tmp["nfc"]["miso"],tmp["nfc"]["rst"],tmp["nfc"]["sda"])
                
                if ("ble" in tmp):
                    self.setBLE()
                
                '''if ("audio" in tmp):
                    self.setAudio(tmp["audio"]["bck"], tmp["audio"]["ws"], tmp["audio"]["sdout"], tmp["audio"]["samplerate"])'''
                
                if ("i2c" in tmp):
                    self.I2CPins = tmp["i2c"]
            else:
                self.log.debug("no config needed for this device")
                
        self.canSend = True

    def getConfig(self, path):
        self.confpath=path
        with open(path, "r") as rf:
            self.config=json.load(rf)
    
    '''
    ### --- ###
    '''

    '''
    ### Notification ###
    '''

    def startNotify(self, click_button_cb):
        self.__old_button_cb = self.__button_cb # will be reused when notification ends
        self.setRecvType('button')
        self.__button_cb = click_button_cb

        self.notifyStarted = True
        
        self.imgOld = self.img
        self.newImg(True)
        self.config["contrast"] = not self.config["contrast"]

    def stopNotify(self):
        self.setRecvType('button')
        self.__button_cb = self.__old_button_cb
        
        self.notifyStarted = False
        
        self.newImg()
        self.img = self.imgOld
        self.config["contrast"] = not self.config["contrast"]
        self.sendImg()

    '''
    ### --- ###
    '''

    '''
    ### Video Stream functions
    '''

    def startStream(self):
        self.__send(self.__packMessage([
            1
        ], 'V'))
    
    def stopStream(self):
        self.__send(self.__packMessage([
            0
        ], 'V'))

    def sendFrame(self, image, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            if image:
                f = io.BytesIO()
                image.save(f, "jpeg")
                buf = f.getbuffer()

                self.__send(self.__packMessage(buf, 'v'))

                del buf
                f.close()
            else:
                self.__send(self.__packMessage(b'0', 'v'))

    '''
    ### --- ###
    '''

    def sendImg(self, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            if(self.heigth and self.width):
                if (self.config["rotation"]):
                    pic=self.img
                else:
                    pic=self.img.rotate(180)

                if(self.config["contrast"] and not(self.ispic) ):
                    pic=ImageOps.colorize(pic, (255,255,255), (0,0,0))
                
                if(self.ispic):
                    self.ispic=False

                if(self.imgIsNew):
                    self.imgIsNew=False
                    pic=pic.convert('1')
                    pic=pic.tobytes()
                    #pic=pic.tobitmap()
                    #pic = bytearray(pic).hex()
                    #print(pic, len(pic))
                    self.__send(self.__packMessage(pic, "S"))
    
    def sendDisplay(self, image, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            f = io.BytesIO()
            image.save(f, "jpeg")
            buf = f.getbuffer()

            self.__send(self.__packMessage(buf, 'd'))

            del buf
            f.close()
    
    def resumeImg(self):
        self.imgIsNew=True
        self.sendImg()

    def setText(self,pos,txt, txt_color, txt_font, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.imgIsNew=True
            self.d.text(pos, txt+" ", txt_color,font=txt_font)

    def setContrast(self, contrast, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.imgIsNew=True
            self.config["contrast"]=contrast
            if(self.confpath):
                with open(self.confpath, "w") as rf:
                    json.dump(self.config, rf)

    def setRotation(self, rotation, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.imgIsNew=True
            self.config["rotation"]=rotation
            if(self.confpath):
                with open(self.confpath, "w") as rf:
                    json.dump(self.config, rf)

    def setCustomParams(self, customParams):
        self.config["custom"] = customParams
        if(self.confpath):
            with open(self.confpath, "w") as rf:
                json.dump(self.config, rf)
    
    def getCustomParams(self):
        if(self.confpath):
            with open(self.confpath, "r") as rf:
                tmp = json.load(rf)
                return tmp["custom"]

    def getFonts(self):
        return self.fonts

    def setImg(self, img, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.imgIsNew=True
            self.img=img.convert('L')
            self.ispic = True

    def addFont(self, font, font_size):
        self.fonts.append(ImageFont.truetype(font, font_size))

    def newImg(self, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.imgIsNew=True
            self.img=Image.new("L",(self.heigth,self.width))
            self.d=ImageDraw.Draw(self.img)
            self.d.rectangle((0,0,self.heigth,self.width),fill=0)
    
    def fillImg(self, img_color, notify=False):
        if((self.notifyStarted and notify) or (not self.notifyStarted)):
            self.imgIsNew=True
            self.d.rectangle((0,0,self.heigth,self.width),fill=img_color)

    def isAlive(self):
        return self.alive
        