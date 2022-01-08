FORMAT = 'utf-8'

class MessageProtocol():
    def __init__(self, type=None, message=None):
        self.type = type
        self.message = message

    def encode(self):
        string  =  self.type+'#'+self.message
        #print("#MESSAGE ENCODE INFO# ", string)
        return string.encode(FORMAT)

    def decode(self, msg):
        string = msg.decode(FORMAT)
        #print("#MESSAGE DECODE INFO# ", string)
        arr = string.split('#')
        self.type = arr[0]
        self.message = arr[1]
        return self