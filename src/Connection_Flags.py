'''
Created on May 30, 2015

@author: Spencer Lee
'''

class ClientFlags:
    Login, Logout, GetMsg, GetSubs, GetFollowers, AddSub, DelSub, Post, HSearch, Quit = range(10)
    
class ServerFlags:
    LogResp, SubResp, Sub, Follow, Post, OldMsg, HashMsg, NewMsg, EndTrans = range(9)