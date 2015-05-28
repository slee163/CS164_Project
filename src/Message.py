'''
Created on May 22, 2015

@author: Spencer Lee
'''

class MessageStatus:
    unread, read = range(2)

class Message(object):

    def __init__(self, params):
        self.poster_id = -1
        self.text = ''
        self.hashtags = []
        
        self.status = MessageStatus.unread
        self.receivers = []
        