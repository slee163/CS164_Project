'''
Created on May 22, 2015

@author: Spencer Lee
'''

import Message
import User
import socket
import select
import sys
import Queue

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
    CreateUser, LogIn, LogOut, Post, Sub, UnSub,  Sync, Quit = range(7)
    
class ServerFlags:
    LogResp, SubResp, Post = range(3)

class TwitServer(object):


    def __init__(self, HOST, PORT):
        self.sock = serverInit(HOST, PORT)
        self.sock.listen(15)
        self.User_List = []
        #self.Connections = []
        self.Read_List = [self.sock]
        self.Write_List = []
        self.message_queues = {}
        self.delimiter = '};{'
        
    def serverFindUser(self, user):
        userMatches = [x for x in self.User_List if x.username == user]
        if not userMatches:
            return None
        else:
            return userMatches[0]
        
    def serverCloseConnection(self, conn):
        '''
        connMatches = [x for x in self.Connections if x[0] == conn]
        for m in connMatches:
            self.Connections.remove(m)
        '''
        if conn in self.Write_List:
            self.Write_List.remove(conn)
            
        if conn in self.Read_List:
            self.Read_List.remove(conn)
            conn.close() 
            
        del self.message_queues[conn]
        
    def serverAddConnection(self, conn, addr):
        connMatches = [x for x in self.Connections if x[0] == conn]
        connTuple = (conn, addr, '')
        if not connMatches:
            self.Connections.append(connTuple)
        else:
            self.serverCloseConnection(conn)
            self.Connections.append(connTuple)
            
        
    def serverResponse(self, conn, context, response):
        reply = ''
        if context == ClientFlags.LogIn or context == ClientFlags.LogOut or context == ClientFlags.CreateUser:
            reply = str(ServerFlags.LogResp) + self.delimiter + str(response)
            
        elif context == ClientFlags.Sub or context == ClientFlags.UnSub:
            reply = str(ServerFlags.SubResp) + self.delimiter + str(response)
            
        elif context == ClientFlags.Post:
            pass
        
        elif context == ClientFlags.Sync:
            pass
        else:
            return
        
        self.message_queues[conn].put(reply)
        if conn not in self.Write_List:
            self.Write_List.append(conn)
    
    def serverClientQuit(self, conn, dataString):
        self.serverCloseConnection(conn)
            
    def serverLogIn(self, conn, logInString):
        breakDown = logInString.split(self.delimiter)
        userMatches = [x for x in self.User_List if x.username == breakDown[1]]
        if not userMatches:
            self.serverResponse(conn, ClientFlags.LogIn, 2)
            return 2
        for m in userMatches:
            if breakDown[2] == m.password:
                m.connection = conn
                '''
                connMatches = [x for x in self.Connections if x[0] == conn]
                for c in connMatches:
                    connTuple = (conn,c[1],m.username)
                    self.Connections.remove(c)
                    self.Connections.append(connTuple)
                '''
                self.serverResponse(conn, ClientFlags.LogIn, 1)
                return 1
        self.serverResponse(conn, ClientFlags.LogIn, 3)
        return 3
    
    def serverLogOut(self, conn, logOutString):
        breakDown = logOutString.split(self.delimiter)
        '''
        addrMatches = [x for x in self.Connections if x[0] == conn and breakDown[1] == x[2]]
        for m in addrMatches:
                self.serverResponse(conn, ClientFlags.LogOut, 1)
                connTuple = (conn,m[1],'')
                self.Connections.remove(m)
                self.Connections.append(connTuple)
                return 1
        '''
        userMatches = [x for x in self.User_List if x.username == breakDown[1]]
        for m in userMatches:
                m.connection = None
                self.serverResponse(conn, ClientFlags.LogOut, 1)
                return 1
        return -1
                
    def serverCreateUser(self, conn, createUserString):
        breakDown = createUserString.split(self.delimiter)
        userMatches= [x for x in self.User_List if x.username == breakDown[1]]
        if userMatches:
            self.serverResponse(conn, ClientFlags.LogOut, 2)
            return 2
        
        newUser = User.User(breakDown[1],breakDown[2])
        self.User_List.append(newUser)
        self.serverResponse(conn, ClientFlags.LogOut, 1)
        return 1
    
    def serverAddUser(self, uname, password):
        newUser = User.User(uname,password)
        self.User_List.append(newUser)
    
    def serverAddSub(self,conn, dataString):
        breakDown = dataString.split(self.delimiter)
        if breakDown[2][0] != '#':
            userMatches = [x for x in self.User_List if x.username == breakDown[2]]
            if not userMatches:
                self.serverResponse(conn, ClientFlags.Sub, -1)
            else:
                users = [x for x in self.User_List if x.username == breakDown[1]]
                for u in users:
                    u.userSub(breakDown[2])
                for u in userMatches:
                    u.userFollow(breakDown[1])
                self.serverResponse(conn, ClientFlags.Sub, 1)
        else:
            users = [x for x in self.User_List if x.username == breakDown[1]]
            for u in users:
                u.userSub(breakDown[2])
            
    def serverUnsub(self,conn, dataString):
        breakDown = dataString.split(self.delimiter)
        userMatches = [x for x in self.User_List if x.username == breakDown[2]]
        if not userMatches:
            self.serverResponse(conn, ClientFlags.UnSub, -1)
        else:
            if breakDown[2][0] != '#':
                users = [x for x in self.User_List if x.username == breakDown[1]]
                for u in users:
                    if breakDown[1] in u.followers:
                        u.userUnfollow(breakDown[2])
                for u in userMatches:
                    u.userUnsub(breakDown[2])
                self.serverResponse(conn, ClientFlags.Sub, 1)
            else:
                for u in userMatches:
                    u.userUnsub(breakDown[2])
    
    def serverPost(self,conn, dataString):
        breakDown = dataString.split(self.delimiter)
        newMessage = Message.Message(breakDown[1], breakDown[2])
        newMessage.status = Message.MessageStatus.read
        
        tags = breakDown[3].split('::')
        newMessage.messageAddHashtags(tags)
        
        receivers = breakDown[4].split('::')
        newMessage.messageAddReceivers(receivers)
        
        '''
        usr = self.serverFindUser(breakDown[1])
        if usr is None:
            return
        else:
            usr.userPostMessage(newMessage)
        '''   
        usr = [x for x in self.User_List if x.username == breakDown[1]][0]
        usr.userPostMessage(newMessage)
            
        newMessage.status = Message.MessageStatus.unread
        if not newMessage.receivers:
            for f in usr.followers:
                follow = [x for x in self.User_List if x.username == f][0]
                if follow is None:
                    continue
                else:
                    follow.userReceivedMessage(newMessage)
                    
            for h in newMessage.hashtags:
                for u in self.User_List:
                    if h in u.hashsubs and u.username not in usr.followers:
                        u.userReceivedMessage(newMessage)
                        
        else:
            for r in newMessage.receivers:
                rcv = [x for x in self.User_List if x.username == r][0]
                if rcv is None:
                    continue
                else:
                    rcv.userReceivedMessage(newMessage)
     
    def serverProcessData(self, conn, data):
        breakDown = data.split(self.delimiter)
        if breakDown[0] == ClientFlags.CreateUser:
            self.serverCreateUser(conn, data)
        elif breakDown[0] == ClientFlags.LogIn:
            self.serverLogIn(conn, data) 
        elif breakDown[0] == ClientFlags.LogOut:
            self.serverLogOut(conn, data)     
        elif breakDown[0] == ClientFlags.Post:
            self.serverPost(conn, data)
        elif breakDown[0] == ClientFlags.Sub:
            self.serverAddSub(conn, data)
        elif breakDown[0] == ClientFlags.Unsub:
            self.serverUnSub(conn,data)
        elif breakDown[0] == ClientFlags.Sync:
            pass
        else:
            return -1
        return 0
       
    def RunServer(self):
        while(1):
            for u in self.User_List:
                if u.connection is None:
                    continue
                else:
                    for m in u.received_messages:
                        if m.status == Message.MessageStatus.unread:
                            message_pkt = str(ServerFlags.Post) + m.messageStringFormat(self.delimiter,'::')
            readable, writeable, errored = select.select(self.Read_List, self.Write_List, [])
            for r in readable:
                if r is self.sock:
                    conn, addr = self.sock.accept()
                    conn.setblocking(0)
                    self.Read_List.append(conn)
                    #self.serverAddConnection(conn, addr)
                    self.message_queues[conn] = Queue.Queue()
                else:
                    data = r.recv(1024)
                    if data:
                        self.serverProcessData(r, data)
                    #Close Connection Cause might need to remove 
                    else:
                        pass
                        #self.serverCloseConnection(r)
                        
            for w in writeable:
                try:
                    next_msg = self.message_queues[w].get_nowait()
                except Queue.Empty:
                    self.Write_List.remove(w)
                else:
                    w.send(next_msg)
            
            for e in errored:
                self.serverCloseConnection(e)
        
