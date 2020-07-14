import numpy
class Menu:
	def __init__(self, app, applications):
		self.app=app
		self.applications=applications
		self.i=0

	def run(self):
		heigth=self.app.heigth
		width=self.app.width
		##self.app=Application("192.168.0.104", 1234, heigth,width)
		n=int(width/10)-1
		pages=int(numpy.ceil(len(self.applications)/n))
		changed=True
		next_app=False
		i_tmp=0
		page=1
		while(1):
			if (changed):
				self.app.newImg()
				self.app.setText((45,0),"MENU "+str(page)+"\\"+str(pages), 255,self.app.getFonts()[0])
				self.app.setText((1,10+(self.i%n)*10),">", 255,self.app.getFonts()[0])
				self.app.setText((10,10),self.applications[n*(page-1)][0], 255,self.app.getFonts()[0])
				for x in range(0,n-1):
					if((page-1)*n+x+1<len(self.applications)):
						self.app.setText((10,10+(x+1)*10),self.applications[(page-1)*n+x+1][0], 255,self.app.getFonts()[0])
				

				self.app.sendImg_and_recvData()
				changed=False
			else:
				self.app.recvData()

			#print(data)	
			if (self.app.isPinUp("DOWN")):
				if(self.i==len(self.applications)-1):
					self.i=0
				else:
					self.i+=1

				page=int(self.i/n)+1
				changed=True
			elif (self.app.isPinUp("UP")):
				if(self.i==0):
					self.i=len(self.applications)-1
				else:
					self.i-=1

				page=int(self.i/n)+1
				changed=True
			elif(self.app.isPinUp("SELECT")):
				i_tmp=self.i
				next_app=True
			
			self.app.storeData()

			if (next_app):
				next_app=False
				print(self.applications[i_tmp][0])
				self.applications[i_tmp][1].run(self)