'''
Created on May 22, 2015

@author: Spencer Lee
'''

class Message(object):

    def __init__(self, user = '', msg = ''):
        self.poster = user
        self.text = msg
        
        self.hashtags = []
        self.receivers = []
        
    def messageAddHashtags(self, tags):
        for t in tags:
            if t != '':
                self.hashtags.append(str(t))
            
    def messageAddReceivers(self, receiver):
        for r in receiver:
            if r != '':
                self.receivers.append(str(r))  
              
    @classmethod
    def fromString(cls, dataString, delimeter = '};{', hashDelimeter = '::', fromClient = False):
        breakDown = dataString.split(delimeter)
        offset = 0
        if fromClient == True:
            offset = 1
        usr = breakDown[1 + offset]
        msg = breakDown[2 + offset]
        m = cls(usr,msg)
        
        tags = breakDown[3 + offset].split(hashDelimeter)
        m.messageAddHashtags(tags)
        
        return m
    
    def printMsg(self):
        print self.poster + ':'
        print self.text
        hashStr = ''
        for h in self.hashtags:
            hashStr += h + ' '
        print hashStr
        print'----------------------------------------------------'

            
    def messageStringFormat(self, delimeter = '};{', hashDelimeter = '::', fromClient = False):
        msgStr = self.poster + delimeter + self.text + delimeter
        for h in self.hashtags:
            msgStr += h + hashDelimeter
        
        msgStr += delimeter    
        if fromClient == True:
            
            for r in self.receivers:
                msgStr += r + hashDelimeter
            
        return msgStr
    
