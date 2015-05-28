'''
Created on May 22, 2015

@author: Spencer Lee
'''

import User
import socket
import select
import sys

def serverInit(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
        print 'Socket create failed'
        print msg
        sys.exit(0)
            
    try:
        sock.bind((host,port))
    except socket.error as msg:
        print 'Socket bind failed'
        print msg
        sock.close()
        sys.exit(0)
    
    return sock

class ClientFlags:
    CreateUser, LogIn, LogOut, Post, Sub, UnSub,  Sync = range(6)
    
class ServerFlags:
    LogResp, SubResp, Sync = range(3)

class TwitServer(object):


    def __init__(self, HOST, PORT):
        self.sock = serverInit(HOST, PORT)
        self.sock.listen(15)
        self.User_List = []
        self.Active_Users = []
        self.Read_List = [self.sock]
        
    def serverResponse(self, conn, addr, context, response):
        if context == ClientFlags.LogIn or context == ClientFlags.LogOut or context == ClientFlags.CreateUser:
            reply = str(ServerFlags.LogResp) + ':' + str(response)
            conn.send(reply)
            
        elif context == ClientFlags.Sub or context == ClientFlags.UnSub:
            reply = str(ServerFlags.SubResp) + ':' + str(response)
            conn.send(reply)
            
        elif context == ClientFlags.Post:
            pass
        
        elif context == ClientFlags.Sync:
            pass
        
    def serverLogIn(self, conn, addr, logInString):
        breakDown = logInString.split(":")
        userMatches = [x for x in self.User_List if x.username == breakDown[1]]
        if not userMatches:
            self.serverResponse(conn, addr, ClientFlags.LogIn, 2)
            return 2
        for m in userMatches:
            if breakDown[2] == m.password:
                connTuple = (conn,addr,m)
                self.Active_Users.append(connTuple)
                self.serverResponse(conn, addr, ClientFlags.LogIn, 1)
                return 1
        self.serverResponse(conn, addr, ClientFlags.LogIn, 3)
        return 3
    
    def serverLogOut(self, conn, addr, logOutString):
        breakDown = logOutString.split(":")
        addrMatches = [x for x in self.Active_User[1] == addr]
        for m in addrMatches:
            if breakDown[1] == m[2].username:
                self.serverResponse(conn, addr, ClientFlags.LogOut, 1)
                self.Active_Users.remove(m)
                conn.close()
                return 1
        return -1
                
    def serverCreateUser(self, conn, addr, createUserString):
        breakDown = createUserString.split(":")
        userMatches= [x for x in self.User_List if x.username == breakDown[1]]
        if userMatches:
            self.serverResponse(conn, addr, ClientFlags.LogOut, 2)
            return 2
        
        newUser = User.User(breakDown[1],breakDown[2])
        self.User_List.append(newUser)
        self.serverResponse(conn, addr, ClientFlags.LogOut, 1)
        return 1
               
        
    def RunServer(self):
        while(1):
            readable, writeable, errored = select.select(self.Read_List, [], [])
            for r in readable:
                if r is self.sock:
                    conn, addr = self.sock.accept()
                    self.Read_List.append(conn)
                else:
                    data = r.recv(1024)
                    
        