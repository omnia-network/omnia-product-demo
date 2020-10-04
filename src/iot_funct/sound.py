import wave

class Sound():
    def __init__(self, username, omnia_controller):
        self.device = 0
        self.username = username
        self.omnia_controller = omnia_controller
        
        self.WAV_FILE = 'src/audio/song.wav'
        #self.SAMPLE_RATE_IN_HZ = 8000

        self.CHUNK_SIZE = 1024

        self.wf = wave.open(self.WAV_FILE,'rb')

        self.sampwidth = self.wf.getsampwidth()
        self.channels = self.wf.getnchannels()
        self.framerate = self.wf.getframerate()

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
                data = self.wf.readframes(self.CHUNK_SIZE)
                if len(data) > 0:
                    self.device.omniacls.sendAudio(data)
                else:
                    return
            
            except (KeyboardInterrupt, Exception) as e:
                print('caught exception {} {}'.format(type(e).__name__, e))
                return
