'''
Created on May 22, 2015

@author: Spencer Lee
'''

class MessageStatus:
    unread, read = range(2)

class Message(object):

    def __init__(self, user = '', msg = ''):
        self.poster = user
        self.text = msg
        
        self.hashtags = []
        self.receivers = []
        
    def messageAddHashtags(self, tags):
        for t in tags:
            self.hashtags.append(str(t))
            
    def messageAddReceivers(self, receiver):
        for r in receiver:
            self.receivers.append(str(r))  
              
    @classmethod
    def fromString(cls, dataString, delimeter = '};{', hashDelimeter = '::'):
        breakDown = dataString.split(delimeter)
        
        usr = breakDown[1]
        msg = breakDown[2]
        m = cls(usr,msg)
        
        tags = breakDown[3].split(hashDelimeter)
        m.messageAddHashtags(tags)
        
        return m
    
    def printMsg(self):
        print self.user + ':'
        print self.text
        hashStr = ''
        for h in self.hashtags:
            hashStr += h + ' '
        print hashStr
        print'--------------------------------------------------------------------------------'

            
    def messageStringFormat(self, delimeter = '};{', hashDelimeter = '::', fromClient = False):
        msgStr = self.poster + delimeter + self.text + delimeter
        for h in self.hashtags:
            msgStr += h + hashDelimeter
            
        if fromClient == True:
            msgStr += delimeter
            for r in self.receivers:
                msgStr += r + hashDelimeter
            
        return msgStr
    
