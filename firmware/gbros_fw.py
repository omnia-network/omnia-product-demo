# firmware v 0.4.1
from machine import Pin, I2C, PWM, ADC
import neopixel
import socket
import framebuf
import time
import struct
import uasyncio

pin_in=[]

oled = ['', '', '']

adc_pin = [-1]

isqc = ['', '', '']

nfc_rdr=[0]

send_type=[0] # 0: data, 1: nfc, 2: adc, 3: i2c


data=b''


async def recv_msg(reader):
    # Read message length and unpack it into an integer
    raw_msglen = await recvall(reader, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return await recvall(reader, msglen)

async def recvall(reader, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        try:
            #sock.setblocking(False)
            packet = await reader.read(n - len(data))
            '''if not packet:
                return None'''
            data.extend(packet)
        except:
            pass
    return data

def run(sock):
    
    reader = uasyncio.StreamReader(sock)
    writer = uasyncio.StreamWriter(sock, {})
    
    print("begin recv cycle")
    
    #isqc = [0, 0, 0]
    
    async def recv(reader):
        args = []
        while True:
            s = bytes(await recv_msg(reader))
            #s=await reader.readline()
            
            print(chr(s[0]))
            
            msg_type = chr(s[0])
            
            msg = None

            if msg_type != 'S':
                msg = s.decode()[1:]
                args = list(map(int, msg.split("-")))
                print(args)
            else:
                msg = s[1:]
            
            if(msg_type == 'f'): # read NFC
                flag = args[0]
                
                if flag:
                    send_type[0]=1
                else:
                    send_type[0]=0

            elif(msg_type == 'I'): # set Input Pin
                pin = args[0]
                if( not ( pin in pin_in)):
                    pin_in.append(pin)
       
            elif(msg_type == 'O'): # set Output Pin
                pin = args[0]
                value = args[1]
                Pin(pin, Pin.OUT).value(value)
                if pin in pin_in:
                    pin_in.remove(pin)

            elif(msg_type == 'A'): # read ADC
                flag = args[0]

                if flag:
                    pin = args[1]
                    adc_pin[0] = pin
                    if pin in pin_in:
                        pin_in.remove(pin)
                    send_type[0] = 2
                else:
                    adc_pin[0] = -1
                    send_type[0] = 0
            
            elif(msg_type == 'i'): # set I2C
                sda_pin = args[0]
                scl_pin = args[1]
                
                #i2c = [0, 0, 0]
                
                isqc[0]=I2C(-1, scl=Pin(scl_pin), sda=Pin(sda_pin))
                
            elif(msg_type == 'c'): # read I2C
                flag = args[0]
                
                if flag:
                    addr = args[1]
                    nbytes = args[2]
                    isqc[1] = addr
                    isqc[2] = nbytes
                    send_type[0]=3
                    print(send_type, isqc)
                else:
                    send_type[0]=0
                
            elif(msg_type == 'P'): # set PWM
                pin = args[0]
                freq = args[1]
                duty = args[2]
                
                PWM(Pin(pin), freq=freq, duty=duty)
                if pin in pin_in:
                    pin_in.remove(pin)    
                        
            elif(msg_type == 'n'): # set NFC
                sclk = args[0]
                mosi = args[1]
                miso = args[2]
                rst = args[3]
                sda = args[4]
                from mfrc522 import MFRC522
                nfc_rdr[0]=MFRC522(sclk, mosi,miso,rst,sda)

            elif(msg_type == 'N'): # set Neopixel
                pin = args[0]
                red = args[1]
                green = args[2]
                blue = args[3]

                np = neopixel.NeoPixel(Pin(pin), 1)
                np[0]=[red,green,blue]
                np.write()
                if pin in pin_in:
                    pin_in.remove(pin)
            
            elif(msg_type == 'D'): #set Display
                sda = args[0]
                scl = args[1]
                oled_height = args[3]
                oled_width = args[2]
                oled[0] = oled_width
                oled[1] = oled_height
                disp = args[4]
                
                i2c = I2C(-1, scl=Pin(scl), sda=Pin(sda))
                print(disp, oled_height, oled_width, sda, scl)

                if(disp==0):
                    from sh1106 import SH1106_I2C
                    oled[2] = SH1106_I2C(oled_width, oled_height, i2c)
                elif(disp==1):
                    from ssd1306 import SSD1306_I2C
                    oled[2] = SSD1306_I2C(oled_width, oled_height, i2c)
            
            elif(msg_type == "S"):
                p=bytearray(msg)
                if oled[0] != '' and oled[1] != '':
                    fbuf=framebuf.FrameBuffer(p, oled[0], oled[1],framebuf.MONO_HLSB)
                    if oled[2] != '':
                        oled[2].blit(fbuf,0,0)
                        oled[2].show()
            
            yield
    
    async def send(writer):
        old_msg = -1
        old_isqc = 0
        while True:
            msg = 0
            if(send_type[0]==0):
                for p in pin_in:
                    msg += ((not Pin(p, Pin.IN, Pin.PULL_UP).value())<<p)

                if(msg != old_msg):
                    old_msg = msg
                    if msg != 0:
                        print("sending", msg)
                        msg=str(msg)+"\n"
                        await writer.awrite(msg.encode())
                    
            elif(send_type[0]==1):
                nfc = '0'
                if(nfc_rdr[0]):
                    (stat, _ ) = nfc_rdr[0].request(nfc_rdr[0].REQIDL)
                    if stat == nfc_rdr[0].OK:
                        (stat, raw_uid) = nfc_rdr[0].anticoll()
                        if stat == nfc_rdr[0].OK:
                            nfc=":%02x%02x%02x%02x:" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
                if nfc !='0':
                    to_send = str(nfc)+"\n"
                    await writer.awrite(to_send.encode())
                
            elif(send_type[0]==2 and adc_pin[0] != -1):
                adc_read = ADC(adc_pin[0])
                await writer.awrite(str(adc_read).encode())
                
            elif(send_type[0]==3):
                #print("reading i2c")
                i2c_msg = 0
                if isqc[0] != '' and isqc[1] != '' and isqc[2] != '':
                    i2c_msg=isqc[0].readfrom(isqc[1], isqc[2])
                    #print(i2c_msg)
                
                if i2c_msg and i2c_msg != old_isqc:
                    old_isqc = i2c_msg
                    to_send = i2c_msg+b'\n'
                    await writer.awrite(to_send)

            #send_type[0]=0
            
            yield
    
    loop = uasyncio.get_event_loop()
    recv_task = loop.create_task(recv(reader))
    send_task = loop.create_task(send(writer))
    
    loop.run_forever()
