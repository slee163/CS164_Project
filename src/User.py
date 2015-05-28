'''
Created on May 22, 2015

@author: Spencer Lee
'''

import Message

class User(object):

    def __init__(self, name = '', pw = '123'):
        self.username = name
        self.password = pw
        self.messages = []
        
        self.subscriptions = []
        self.followers = []
        