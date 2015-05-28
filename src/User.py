'''
Created on May 22, 2015

@author: Spencer Lee
'''

import Message
import socket

class User(object):

    def __init__(self, name = '', pw = '123'):
        self.username = name
        self.password = pw
        self.posted_messages = []
        self.received_messages = []
        
        self.connection = None
        self.address = ''
        
        self.subscriptions = []
        self.followers = []
    
    def userPostMessage(self, msg):
        self.posted_messages.append(msg)
    
    def userReceivedMessage(self, msg):
        self.received_messages.append(msg)
        
    def userSub(self, name):
        if name in self.subscriptions:
            pass
        else:
            self.subscriptions.append(name)
        
    def userUnsub(self, name):
        if name not in self.subscriptions:
            pass
        else:
            self.subscriptions.remove(name)