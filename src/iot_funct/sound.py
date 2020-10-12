import wave
import json
import struct
import numpy

class Sound():
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        self.sharing = self.omnia_controller.omnia_media_sharing
        
        #self.WAV_FILE = 'src/audio/song.wav'
        #self.SAMPLE_RATE_IN_HZ = 8000
        with open("src/iot_funct/resources/playlist.json", "r") as p:
            self.playlist = json.load(p)
        
        self.pl_index = "0"

        self.CHUNK_SIZE = 10000

        self.wf = wave.open(self.playlist["0"]["path"],'rb')

        self.song_name = self.playlist["0"]["name"]
        self.song_author = self.playlist["0"]["author"]
        self.song_cover = self.playlist["0"]["cover"]

        self.sampwidth = self.wf.getsampwidth()
        self.channels = self.wf.getnchannels()
        self.framerate = self.wf.getframerate()
        self.nframes = self.wf.getnframes() / 64    # 64 = 4 (frame lenght) * 16 (bits per frame)

        self.time_sleep = self.CHUNK_SIZE / self.framerate

        self.duration = self.nframes / float(self.framerate)
        self.elapsed_time = 0.0

        self.sharing.setAttribute(self.username, "elapsed_time", self.elapsed_time)
        self.sharing.setAttribute( self.username, "duration", self.duration)

    def getNotificationMessage(self, deviceName, username=None):

        msg = []

        msg.append([(10, 35), deviceName.replace("_", " ").upper()])
        msg_status = "START STREAM?"
        
        msg.append([(10,50), msg_status])

        return msg
    
    def handleStreaming(self, device):
        if self.device!=device:
            old_device = self.device
            self.__setDevice(device)
            if old_device != 0:
                old_device.omniacls.newImg()
                old_device.omniacls.sendImg()
                old_device.resetStreamingUser()
    
    def __setDevice(self, device):
        self.device = device
    
    def start(self):
        self.device.omniacls.startAudio(self.framerate, self.channels, self.sampwidth, self.CHUNK_SIZE)
    
    def stop(self):
        pass

    def scaleSample(self, x, volume):
        return (x*volume)//10

    def calculateVolume(self, data, volume):
        if volume != 0:
            data = numpy.frombuffer(data, numpy.int16) // 20 * volume
            #i_data = [self.scaleSample(x,volume) for x in data]

            return struct.pack('h'*len(data), *data)
        else:
            return b'0'

    
    def changeSong(self, pl_object):
        self.wf = wave.open(pl_object["path"],'rb')
                            
        self.song_name = pl_object["name"]
        self.song_author = pl_object["author"]
        self.song_cover = pl_object["cover"]

        self.sampwidth = self.wf.getsampwidth()
        self.channels = self.wf.getnchannels()
        self.framerate = self.wf.getframerate()
        self.nframes = self.wf.getnframes() / 64    # 64 = 4 (frame lenght) * 16 (bits per frame)

        self.time_sleep = self.CHUNK_SIZE / self.framerate

        self.duration = self.nframes / float(self.framerate)
        self.elapsed_time = 0.0

        self.sharing.setAttribute(self.username, "elapsed_time", self.elapsed_time)
        self.sharing.setAttribute( self.username, "duration", self.duration)
    
    def run(self):        

        if self.device:

            try:
                pause = self.sharing.getAttribute(self.username, "pause")

                if pause is None:
                    pause = True

                volume = self.sharing.getAttribute(self.username, "volume")

                if volume is None:
                    volume = 5

                prev = self.sharing.getAttribute(self.username, "prev")

                next = self.sharing.getAttribute(self.username, "next")

                if prev:
                    self.sharing.setAttribute(self.username, "prev", False)
                    if self.elapsed_time > 10.0:
                        self.wf.rewind()
                        self.elapsed_time = 0
                        self.sharing.setAttribute(self.username, "elapsed_time", self.elapsed_time)
                    else:
                        index = int(self.pl_index)
                        if index > 0:
                            self.pl_index = str(index-1)
                            self.sharing.setAttribute(self.username, "song_id", self.pl_index)
                            self.changeSong(self.playlist[self.pl_index])
                        else:
                            self.wf.rewind()
                            self.elapsed_time = 0
                            self.sharing.setAttribute(self.username, "elapsed_time", self.elapsed_time)
                elif next:
                    self.sharing.setAttribute(self.username, "next", False)
                    index = int(self.pl_index)

                    if not index == len(self.playlist) - 1:
                        self.pl_index = str(index+1)
                        self.sharing.setAttribute(self.username, "song_id", self.pl_index)
                        self.changeSong(self.playlist[self.pl_index])

                if not pause:
                    data = self.wf.readframes(self.CHUNK_SIZE)

                    data = self.calculateVolume(data, volume)
                    
                    if len(data) > 0:
                        if data != b'0':
                            self.device.omniacls.sendAudio(data)
                        
                        self.elapsed_time += self.time_sleep

                        self.sharing.setAttribute(self.username, "elapsed_time", self.elapsed_time)
                    else:
                        pass
            
            except (KeyboardInterrupt, Exception) as e:
                print('caught exception {} {}'.format(type(e).__name__, e))
                return
