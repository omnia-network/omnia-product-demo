import socket
from PIL import Image, ImageDraw, ImageFont, ImageOps
import time
import json
import sys

class Application:

	def __init__(self, adress, port, username, timesleep):
		self.heigth=0
		self.width=0
		self.username = username
		self.fonts = [ImageFont.truetype("Arial.ttf",11),ImageFont.truetype("Arial.ttf",30)]
		self.img=Image.new("L",(self.heigth,self.width))
		self.d=ImageDraw.Draw(self.img)
		self.d.rectangle((0,0,self.heigth,self.width),fill=0)
		self.addr=(adress, port)
		self.so=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.so.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.so.bind(self.addr)
		self.so.listen(1)
		self.so.settimeout(120)
		self.timesleep=timesleep
		self.confpath=""
		self.config={"contrast": 0,  "rotation": 0}
		self.sc=0
		self.data=0
		self.data_old=0
		self.ispic=False
		self.neoPins=[15]
		self.inPins = {}
		self.outPins = {}
		self.pwmPins= {}

	def __send(self,data):
		self.sc.send(data)
		self.sc.close()

	def __recv(self):
		try:
			self.sc, adr=self.so.accept()
		except:
			sys.exit()
		
		self.sc.settimeout(self.timesleep)
		try:
			self.data=int(self.sc.recv(1024))
		except:
			pass

		return self.data
	
	def getPinConfig(self, path):
		with open(path, "r") as rf:
			tmp = json.load(rf)
			self.inPins = tmp["in"]
			self.outPins = tmp["out"]
			self.setInPins()
			if("pwm" in tmp):
				self.pwmPins= tmp["pwm"]

			for neo in tmp["neopixel"]:
				self.setNeoPin(tmp["neopixel"][neo]["number"])

			if(tmp["display"]):
				self.heigth=tmp["display"]["heigth"]
				self.width=tmp["display"]["width"]
				self.setDisplqy(tmp["display"]["sda"], tmp["display"]["scl"], self.heigth, self.width)


	def getConfig(self, path):
		self.confpath=path
		with open(path, "r") as rf:
			self.config=json.load(rf)

	def setInPins(self):
		for pin in self.inPins:
			self.setInPin(self.inPins[pin]['number'])

	def setNeoPin(self, pin):
		self.neoPins.append(pin)

	def setOutPin(self, pin, value):
		self.__recv()
		self.__send(str(pin*10+int(not value)).encode())
		time.sleep(self.timesleep)

	def setInPin(self, pin):
		self.__recv()
		self.__send(str(pin).encode())
		time.sleep(self.timesleep)

	def setDisplqy(self, sda, scl, heigth, width):
		self.heigth = heigth
		self.width = width
		self.__recv()
		self.__send((str(sda).zfill(2)+str(scl).zfill(2)+str(heigth).zfill(3)+str(width).zfill(3)).encode())
		time.sleep(self.timesleep)
		
	def setNeopixel(self, status, pin=-1):
		if(len(self.neoPins)):
			self.__recv()
			if(pin==-1):
				self.__send((str(self.neoPins[0]).zfill(2)+str(status[0]).zfill(3)+str(status[1]).zfill(3)+str(status[2]).zfill(3)).encode())
			elif(pin in self.neoPins):
				self.__send((str(pin).zfill(2)+str(status[0]).zfill(3)+str(status[1]).zfill(3)+str(status[2]).zfill(3)).encode())
			else:
				self.__send(b'')

			time.sleep(self.timesleep)

	def setPwm(self, pin, freq, duty):
		self.__recv()
		self.__send((str(pin).zfill(2)+str(freq).zfill(3)+str(duty).zfill(4)).encode())
		time.sleep(self.timesleep)

	def recvData(self):
		self.data=int(self.__recv())
		self.__send(b'')
		time.sleep(self.timesleep)
		buttons={}
		for pin in self.inPins:
			if(self.data & 1<<self.inPins[pin]["number"]):
				buttons[pin]=1
			else:
				buttons[pin]=0
		print(buttons)
		return self.data

	def sendImg_and_recvData(self):
		if (self.config["rotation"]):
			pic=self.img
		else:
			pic=self.img.rotate(180)

		if(self.config["contrast"] and not(self.ispic)):
			pic=ImageOps.colorize(pic, (255,255,255), (0,0,0))
		
		if(self.ispic):
			self.ispic=False

		pic=pic.convert('1')
		pic=pic.tobytes()
		self.data=int(self.__recv())
		buttons={}
		#time.sleep(self.timesleep)
		if(self.heigth and self.width):
			self.__send(pic)
		else:
			self.__send(b'')

		time.sleep(self.timesleep)
		for pin in self.inPins:
			if(self.data & 1<<self.inPins[pin]["number"]):
				buttons[pin]=1
			else:
				buttons[pin]=0
		print(buttons)

		return self.data

	def sendImg(self):
		if(self.heigth and self.width):
			if (self.config["rotation"]):
				pic=self.img
			else:
				pic=self.img.rotate(180)

			if(self.config["contrast"] and not(self.ispic) ):
				pic=ImageOps.colorize(pic, (255,255,255), (0,0,0))
			
			if(self.ispic):
				self.ispic=False

			pic=pic.convert('1')
			pic=pic.tobytes()
			self.__recv()
			self.__send(pic)
			time.sleep(self.timesleep)
	
	def isPinUp(self, btn_name):
		#print(self.data_old, self.data)
		flag = False
		if(self.data_old!=self.data) and (self.data & 1<<self.inPins[btn_name]["number"]):
			flag=True
		return flag
	
	def storeData(self):
		if(self.data!=self.data_old):
			self.data_old = self.data
	
	def resetData(self):
		self.data_old = 0

	def setText(self,pos,txt, txt_color, txt_font):
		self.d.text(pos, txt, txt_color,font=txt_font)

	def setContrast(self, contrast):
		self.config["contrast"]=contrast
		with open(self.confpath, "w") as rf:
			json.dump(self.config, rf)

	def setRotation(self, rotation):
		self.config["rotation"]=rotation
		with open(self.confpath, "w") as rf:
			json.dump(self.config, rf)

	def getFonts(self):
		return self.fonts

	def setImg(self, img):
		self.img=img.convert('L')
		self.ispic = True

	def addFont(self, font, font_size):
		self.fonts.append(ImageFont.truetype(font, font_size))

	def newImg(self):
		self.img=Image.new("L",(self.heigth,self.width))
		self.d=ImageDraw.Draw(self.img)
		self.d.rectangle((0,0,self.heigth,self.width),fill=0)

	def fillImg(self, img_color):
		self.d.rectangle((0,0,self.heigth,self.width),fill=img_color)

