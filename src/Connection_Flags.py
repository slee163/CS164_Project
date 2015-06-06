'''
Created on May 30, 2015

@author: Spencer Lee
'''

class ClientFlags:
    Login, Logout, GetMsg, GetSubs, GetFollowers, AddSub, DelSub, Post, HSearch, Quit, MSize = range(11)
    
class ServerFlags:
    Login, SubResp, Sub, Follow, OldMsg, HashMsg, NewMsg, EndTrans, MSize = range(9)