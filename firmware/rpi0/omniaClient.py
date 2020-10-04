# firmware v 0.5.1
import socket
import struct
import asyncio
from bleak import BleakScanner

class OmniaClient:
    def __init__(self, socket, device_type, touch=None):
        self.pin_in = []
        self.oled = None
        self.adc_pin = None
        self.isqc = None
        self.nfc_rdr = None
        
        self.audio_out = None
        self.send_type = None  # 0: touch, 1: nfc, 2: adc, 3: i2c, 4: ble

        ## Asyncio ##
        self.loop = asyncio.new_event_loop()

        ## Socket ##
        self.reader, self.writer = self.loop.run_until_complete(asyncio.open_connection(sock=socket))

        ## BLE ##
        self.stopScan = False
        self.ble = None
        self.bleDevices = []
        self.ble_task = None

        ## Received Data ##
        self.received_data = None
        self.stop = False

        ## Display ##
        self.display = None

        ## Audio ##
        self.audio = None

        ## Touch ##
        self.touch = None

        self.init_type(device_type, touch)
    
    def init_type(self, device_type, touch):
        ## Device Type ##
        if device_type == "ili9341":
            from screen import Screen

            self.display = Screen()
        elif device_type == "audio":
            from audio import Audio

            self.audio = Audio()
        
        ## Touch ##
        if touch == 'xpt2046':
            from touch import TouchScreen

            self.touch = TouchScreen()
            self.send_type = 0

    async def recv_msg(self):
        # Read message length and unpack it into an integer
        raw_msglen = await self.recvall(4)
        if not raw_msglen:
            return b'00'
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return await self.recvall(msglen)

    async def recvall(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            try:
                #sock.setblocking(False)
                packet = await self.reader.read(n - len(data))
                '''if not packet:
                    return None'''
                data.extend(packet)
            except:
                pass
        return data

    async def scan_ble(self):
        while not self.stopScan:
            async with BleakScanner() as scanner:
                await asyncio.sleep(2.0)
                self.bleDevices = await scanner.get_discovered_devices()
            '''for d in devices:
                print(d)'''

    def run(self):
        
        recv_task = self.loop.create_task(self.recv())
        send_task = self.loop.create_task(self.send())
        
        self.loop.run_forever()
    
    async def recv(self):
        print("begin recv cycle")
        args = []
        while True:
            s = bytes(await self.recv_msg())
            #s=await reader.readline()
            
            print(chr(s[0]))
            
            msg_type = chr(s[0])
            
            msg = None

            if msg_type != 'S' and msg_type != 'j' and msg_type != 'v' and msg_type != 'a' and msg_type != 'd':
                msg = s.decode()[1:]
                args = list(map(int, msg.split("-")))
                print(args)
            else:
                msg = s[1:]
            
            if(msg_type == 'b'):    # scan BLE
                flag = args[0]

                self.stopScan = not flag
                
                if flag:
                    self.send_type = 4
                    self.ble_task = self.loop.create_task(self.scan_ble())
                else:
                    self.ble_task.cancel()
                    self.send_type = 0
                    self.bleDevices = []
            
            elif(msg_type == 'V'):  # stream video
                flag = args[0]
                
                self.display.stopStream = not flag

                self.loop.create_task(self.display.draw_stream())
                #self.display.startStream()
            
            elif(msg_type == 'v'):  # recv video frame
                self.received_data = msg

                if self.display:
                    self.loop.create_task(self.display.recv_frame(msg))

            elif(msg_type == 'A'):  # start audio
                flag = args[0]

                if flag:
                    framerate = args[1]
                    channels = args[2]
                    sampwidth = args[3]
                    chunk_size = args[4]

                    if self.audio:
                        self.audio.start_stream(framerate, channels, sampwidth, chunk_size)
                else:
                    if self.audio:
                        self.audio.stop_stream()
            
            elif(msg_type == 'a'):  # recv audio frame
                if self.audio:
                    self.audio.stream_audio(msg)
            
            elif(msg_type == 'd'):  # recv display
                self.received_data = msg

                if self.display:
                    self.display.setDisplay(msg)
                    print("done")
            
            await asyncio.sleep(0.01)
        print("end recv")
    
    async def send(self):
        print("begin send cycle")
        old_msg = ''
        while True:
            #print(self.send_type)
            msg = ''
            if(self.send_type == 0):
                x, y = self.touch.get_touch_coords()
                #print(x,y)

                if x > 0 and y > 0:
                    msg = str(x) + "," + str(y)
                    
            elif(self.send_type == 4):
                ble_result = ''
                for d in self.bleDevices:
                    ble_result += str(d.rssi)+'+'+str(d.name)+","
                msg = ble_result
            
            if msg is not '' and msg != old_msg:
                old_msg = msg
                to_send = msg.encode()
                to_send += b'\n'
                print(to_send)
                self.writer.write(to_send)

            await self.writer.drain()
            
            await asyncio.sleep(0.1)
        print("end send")
