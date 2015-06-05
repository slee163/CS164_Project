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

        self.offlineMessages = []
        
        self.connection = None
        self.address = ''
        self.address = ''
        
        self.subscriptions = []
        self.hashsubs = []
        self.followers = []
    
    
    def userReceivedOfflineMessage(self, msg):
        self.offlineMessages.append(msg)
        
    def userSub(self, name):
        if name[0] != '#':
            if name in self.subscriptions:
                pass
            else:
                self.subscriptions.append(name)
        else:
            if name in self.hashsubs:
                pass
            else:
                self.hashsubs.append(name)
        
    def userUnsub(self, name):
        if name[0] != '#':
            if name not in self.subscriptions:
                pass
            else:
                self.subscriptions.remove(name)
        else:
            if name not in self.hashsubs:
                pass
            else:
                self.hashsubs.remove(name)
            
    def userFollow(self, name):
        if name in self.followers:
            pass
        else:
            self.followers.append(name)
    
    def userUnfollow(self,name):
        if name not in self.followers:
            pass
        else:
            self.followers.remove(name)

