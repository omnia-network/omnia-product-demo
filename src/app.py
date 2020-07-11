import socket
from PIL import Image, ImageDraw, ImageFont, ImageOps
import time
import json

class Application:

	def __init__(self, adress, port, heigth,width):
		self.heigth=heigth
		self.width=width
		self.fonts = [ImageFont.truetype("Arial.ttf",11),ImageFont.truetype("Arial.ttf",30)]
		self.img=Image.new("L",(self.heigth,self.width))
		self.d=ImageDraw.Draw(self.img)
		self.d.rectangle((0,0,self.heigth,self.width),fill=0)
		self.addr=(adress, port)
		self.contrast=0
		self.rotation=0
		self.so=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.so.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.so.bind(("0.0.0.0", 1234))
		self.so.listen(1)
		self.sc=0
		self.data=0
		self.inPins = {}
		self.outPins = {}

	def __send(self,data):
		self.sc.send(data)
		self.sc.close()

	def __recv(self):
		self.sc, adr=self.so.accept()
		self.sc.settimeout(0.01)
		try:
			self.data=self.sc.recv(1024)
		except:
			pass

		return self.data
	
	def getPinConfig(self, path):
		with open(path, "r") as rf:
			tmp = json.load(rf)
			self.inPins = tmp["in"]
			self.outPins = tmp["out"]
	
	def setInPins(self):
		for pin in self.inPins:
			self.setInPin(self.inPins[pin]['number'])
	
	def sendImg(self):
		if (self.rotation):
			pic=self.img
		else:
			pic=self.img.rotate(180)
		
		if(self.contrast):
			pic=ImageOps.colorize(pic, (255,255,255), (0,0,0))

		pic=pic.convert('1')
		pic=pic.tobytes()
		self.__recv()
		#time.sleep(0.05)
		self.__send(pic)
		time.sleep(0.1)

	def setOutPin(self, pin, value):
		self.__recv()
		#time.sleep(0.05)
		self.__send(str(pin*10+int(not value)).encode())
		time.sleep(0.1)

	def setInPin(self, pin):
		self.__recv()
		#time.sleep(0.05)
		self.__send(str(pin).encode())
		time.sleep(0.1)

	def recvData(self):
		data=self.__recv()
		#time.sleep(0.05)
		self.__send(b'')
		time.sleep(0.1)
		return data

	def setLed(self, status):
		self.__recv()
		#time.sleep(0.05)
		self.__send(str(int(status)).encode())
		time.sleep(0.1)

	def setNeopixel(self, status):
		self.__recv()
		#time.sleep(0.05)
		self.__send((str(status[0]).zfill(3)+str(status[1]).zfill(3)+str(status[2]).zfill(3)).encode())
		time.sleep(0.1)

	def sendImg_and_recvData(self):
		if (self.rotation):
			pic=self.img
		else:
			pic=self.img.rotate(180)

		if(self.contrast):
			pic=ImageOps.colorize(pic, (255,255,255), (0,0,0))

		pic=pic.convert('1')
		pic=pic.tobytes()
		data=self.__recv()
		#time.sleep(0.05)
		self.__send(pic)
		time.sleep(0.1)
		return data

	def setText(self,pos,txt, txt_color, txt_font):
		self.d.text(pos, txt, txt_color,font=txt_font)

	def setContrast(self, contrast):
		self.contrast = int(contrast)

	def setRotation(self, rotation):
		self.rotation = int(rotation)

	def getFonts(self):
		return self.fonts

	def setImg(self, img):
		self.img=img.convert('L')

	def addFont(self, font, font_size):
		self.fonts.append(ImageFont.truetype(font, font_size))

	def newImg(self):
		self.img=Image.new("L",(self.heigth,self.width))
		self.d=ImageDraw.Draw(self.img)
		self.d.rectangle((0,0,self.heigth,self.width),fill=0)

	def fillImg(self, img_color):
		self.d.rectangle((0,0,self.heigth,self.width),fill=img_color)

