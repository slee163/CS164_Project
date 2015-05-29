'''
Created on May 22, 2015

@author: Spencer Lee
'''

class MessageStatus:
    unread, read = range(2)

class Message(object):

    def __init__(self, user = '', msg = ''):
        self.poster = ''
        self.text = ''
        self.status = MessageStatus.unread
        
        self.hashtags = []
        self.receivers = []
    
    def messageAddHashtags(self, *tags):
        for t in tags:
            self.hashtags.append(t)
            
    def messageAddReceivers(self, *receiver):
        for r in receiver:
            self.receivers.append(r)
            
    def messageStringFormat(self, delimeter = '};{', hashDelimeter = '::'):
        msgStr = self.poster + delimeter + self.text + delimeter
        for h in self.hashtags:
            msgStr += h + hashDelimeter
        return msgStr
