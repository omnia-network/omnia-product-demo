import wave

class Sound():
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        self.sharing = self.omnia_controller.omnia_media_sharing
        
        self.WAV_FILE = 'src/audio/song.wav'
        #self.SAMPLE_RATE_IN_HZ = 8000

        self.CHUNK_SIZE = 10000

        self.wf = wave.open(self.WAV_FILE,'rb')

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
    
    def run(self):        

        if self.device:

            try:
                pause = self.sharing.getAttribute(self.username, "pause")

                prev = self.sharing.getAttribute(self.username, "prev")

                if prev:
                    self.wf.rewind()
                    self.sharing.setAttribute(self.username, "prev", False)
                    self.elapsed_time = 0
                    self.sharing.setAttribute(self.username, "elapsed_time", self.elapsed_time)
                
                if not pause:
                    data = self.wf.readframes(self.CHUNK_SIZE)
                    
                    if len(data) > 0:
                        self.device.omniacls.sendAudio(data)
                        self.elapsed_time += self.time_sleep

                        self.sharing.setAttribute(self.username, "elapsed_time", self.elapsed_time)
                    else:
                        pass
            
            except (KeyboardInterrupt, Exception) as e:
                print('caught exception {} {}'.format(type(e).__name__, e))
                return
